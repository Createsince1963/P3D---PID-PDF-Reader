"""Windows mobile hotspot (own Wi-Fi for a limited office area) - check, start, stop (0.9.7).

Python standard library only: the Windows Runtime API NetworkOperatorTetheringManager (the same one Settings >
Mobile hotspot uses) is called through Windows PowerShell 5.1; the result comes back as JSON. No package, no admin
rights, no change to network settings beyond switching the hotspot on / off.

* check()  read-only: Wi-Fi adapter / driver, Wi-Fi Direct, group policies, domain, tethering capability, state,
           SSID / password, clients, the hotspot's own IPv4 address (usually 192.168.137.1).
* start() / stop(): switch the hotspot on / off. Windows always SHARES a connection (the current WLAN / LAN) with the
           hotspot - devices in the hotspot can reach that network too. On a company laptop: IT approval first.
"""
from __future__ import annotations

import json
import re
import secrets
import subprocess

HOTSPOT_DEFAULT_IP = "192.168.137.1"      # Windows Internet Connection Sharing default address of the hotspot adapter
DEFAULT_SSID = "P3D-PDFREADER"
BANDS = {"2.4": "TwoPointFourGigahertz", "auto": "Auto", "5": "FiveGigahertz"}
_PW_CHARS = "abcdefghjkmnpqrstuvwxyz23456789"      # no l / 1 / i / o / 0: nothing to confuse when typing on a phone
SSID_RE = re.compile(r"[A-Za-z0-9 _.\-]{1,32}")
PASSWORD_RE = re.compile(r"[A-Za-z0-9_.\-!#+*]{8,63}")


def new_password(length: int = 10) -> str:
    """Easy-to-type WPA2 password: lowercase letters and digits only, no confusable characters."""
    return "".join(secrets.choice(_PW_CHARS) for _ in range(length))


def validate(ssid: str, password: str) -> str:
    """'' = fine, else the reason (shown to the user). Restricted characters also keep the PowerShell text safe."""
    if not SSID_RE.fullmatch(ssid or ""):
        return "Wi-Fi name: 1-32 characters, only letters, digits, space, _ . -"
    if not PASSWORD_RE.fullmatch(password or ""):
        return "Password: 8-63 characters, only letters, digits and _ . - ! # + * (no spaces, no brackets)"
    return ""

_PS_COMMON = r"""
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$out = [ordered]@{ ok = $true; error = '' }
function Load-Tethering {
    Add-Type -AssemblyName System.Runtime.WindowsRuntime
    $null = [Windows.Networking.Connectivity.NetworkInformation, Windows.Networking.Connectivity, ContentType = WindowsRuntime]
    $null = [Windows.Networking.NetworkOperators.NetworkOperatorTetheringManager, Windows.Networking.NetworkOperators, ContentType = WindowsRuntime]
    $p = [Windows.Networking.Connectivity.NetworkInformation]::GetInternetConnectionProfile()
    if ($null -eq $p) { $p = @([Windows.Networking.Connectivity.NetworkInformation]::GetConnectionProfiles() | Where-Object { $_.GetNetworkConnectivityLevel() -ne 'None' })[0] }
    return $p
}
function Await($op, [Type]$type) {
    $m = [System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {
        $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' } | Select-Object -First 1
    $t = $m.MakeGenericMethod($type).Invoke($null, @($op))
    if (-not $t.Wait(60000)) { throw 'Windows did not answer within 60 s' }
    return $t.Result
}
function AwaitAction($op) {
    $m = [System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {
        $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncAction' } | Select-Object -First 1
    $t = $m.Invoke($null, @($op))
    if (-not $t.Wait(60000)) { throw 'Windows did not answer within 60 s' }
}
function State($mgr) {
    $cfg = $mgr.GetCurrentAccessPointConfiguration()
    $out.state = [string]$mgr.TetheringOperationalState
    $out.ssid = $cfg.Ssid
    $out.password = $cfg.Passphrase
    $out.clients = $mgr.ClientCount
    $out.max_clients = $mgr.MaxClientCount
    try { $out.band = [string]$cfg.Band } catch { $out.band = '' }
    try { $out.security = [string]$cfg.AuthenticationKind } catch { $out.security = '' }
    try { $out.auto_off = [Windows.Networking.NetworkOperators.NetworkOperatorTetheringManager]::IsNoConnectionsTimeoutEnabled() } catch { $out.auto_off = $null }
    $ip = Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue | Where-Object {
        (Get-NetAdapter -InterfaceIndex $_.InterfaceIndex -ErrorAction SilentlyContinue).InterfaceDescription -like '*Wi-Fi Direct*' } |
        Select-Object -First 1
    $out.ip = if ($ip) { $ip.IPAddress } else { '' }
}
"""

_PS_CHECK = _PS_COMMON + r"""
try {
    $w = Get-NetAdapter -Physical -ErrorAction SilentlyContinue | Where-Object { $_.PhysicalMediaType -like '*802.11*' } | Select-Object -First 1
    $out.wifi_adapter = if ($w) { $w.InterfaceDescription } else { '' }
    $out.wifi_status = if ($w) { [string]$w.Status } else { '' }
    $out.wifi_direct = @(Get-PnpDevice -FriendlyName '*Wi-Fi Direct Virtual Adapter*' -ErrorAction SilentlyContinue).Count
    $cs = Get-CimInstance Win32_ComputerSystem
    $out.domain = if ($cs.PartOfDomain) { $cs.Domain } else { '' }
    $pol = @()
    foreach ($k in 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\Network Connections', 'HKLM:\SOFTWARE\Policies\Microsoft\Windows\TetheringPolicy') {
        if (Test-Path $k) {
            $v = Get-ItemProperty $k
            foreach ($n in 'NC_ShowSharedAccessUI', 'NC_AllowNetBridge_NLA', 'AllowTethering') {
                if ($null -ne $v.$n) { $pol += "$n=$($v.$n)" }
            }
        }
    }
    $out.policies = $pol -join ', '
    $p = Load-Tethering
    $out.shared_connection = if ($p) { $p.ProfileName } else { '' }
    if ($p) {
        $out.capability = [string][Windows.Networking.NetworkOperators.NetworkOperatorTetheringManager]::GetTetheringCapabilityFromConnectionProfile($p)
        State ([Windows.Networking.NetworkOperators.NetworkOperatorTetheringManager]::CreateFromConnectionProfile($p))
    } else {
        $out.capability = 'NoConnectionToShare'
    }
} catch { $out.ok = $false; $out.error = $_.Exception.Message }
$out | ConvertTo-Json -Compress
"""

_PS_SWITCH = _PS_COMMON + r"""
try {
    $p = Load-Tethering
    if ($null -eq $p) { throw 'No network connection to share - Windows needs an active WLAN / LAN connection for the mobile hotspot.' }
    $T = [Windows.Networking.NetworkOperators.NetworkOperatorTetheringManager]
    $mgr = $T::CreateFromConnectionProfile($p)
    if ('__ACTION__' -eq 'start' -and '__SSID__' -ne '') {         # compatible settings: own name / password, WPA2, band
        if ([string]$mgr.TetheringOperationalState -eq 'On') { $null = Await ($mgr.StopTetheringAsync()) ([Windows.Networking.NetworkOperators.NetworkOperatorTetheringOperationResult]); Start-Sleep -Milliseconds 800 }
        $c = $mgr.GetCurrentAccessPointConfiguration()
        $c.Ssid = '__SSID__'
        $c.Passphrase = '__PASSWORD__'
        try { $c.AuthenticationKind = 'Wpa2' } catch { }
        if ('__BAND__' -ne '') { try { if ($c.IsBandSupported('__BAND__')) { $c.Band = '__BAND__' } } catch { } }
        AwaitAction ($mgr.ConfigureAccessPointAsync($c))
    }
    if ('__KEEP__' -eq 'on') { $out.auto_off_before = $T::IsNoConnectionsTimeoutEnabled(); $T::DisableNoConnectionsTimeout() }
    if ('__KEEP__' -eq 'restore') { $T::EnableNoConnectionsTimeout() }
    $op = if ('__ACTION__' -eq 'start') { $mgr.StartTetheringAsync() } else { $mgr.StopTetheringAsync() }
    $r = Await $op ([Windows.Networking.NetworkOperators.NetworkOperatorTetheringOperationResult])
    $out.result = [string]$r.Status
    $out.message = $r.AdditionalErrorMessage
    if ([string]$r.Status -ne 'Success') { $out.ok = $false; $out.error = "Windows: $($r.Status) $($r.AdditionalErrorMessage)".Trim() }
    Start-Sleep -Milliseconds 1500
    State $mgr
    $out.shared_connection = $p.ProfileName
} catch { $out.ok = $false; $out.error = $_.Exception.Message }
$out | ConvertTo-Json -Compress
"""


def _run(script: str, timeout: int = 90) -> dict:
    try:
        cp = subprocess.run(["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script],
                            capture_output=True, timeout=timeout, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except (OSError, subprocess.SubprocessError) as e:
        return {"ok": False, "error": f"PowerShell could not be run: {e}"}
    text = cp.stdout.decode("utf-8", errors="replace").strip()
    line = next((ln for ln in reversed(text.splitlines()) if ln.startswith("{")), "")
    try:
        return json.loads(line)
    except ValueError:
        err = cp.stderr.decode("utf-8", errors="replace").strip() or text or f"exit code {cp.returncode}"
        return {"ok": False, "error": f"Unexpected PowerShell answer: {err[:400]}"}


def check() -> dict:
    """Read-only check of hotspot capability and current state (see module docstring)."""
    return _run(_PS_CHECK)


def _switch(action: str, ssid: str = "", password: str = "", band: str = "", keep: str = "") -> dict:
    if ssid or password:
        err = validate(ssid, password)
        if err:
            return {"ok": False, "error": err}
    script = (_PS_SWITCH.replace("__ACTION__", action).replace("__SSID__", ssid.replace("'", "''"))
              .replace("__PASSWORD__", password.replace("'", "''")).replace("__BAND__", BANDS.get(band, ""))
              .replace("__KEEP__", keep))
    return _run(script)


def start(ssid: str = "", password: str = "", band: str = "2.4", keep_on: bool = True) -> dict:
    """Switch the Windows mobile hotspot on (shares the current connection). With `ssid` / `password`: first set the
    compatible configuration - that name and password, WPA2, `band` ('2.4' = most compatible, 'auto', '5').
    `keep_on`: switch Windows' "turn off when no device is connected" (after about 5 min) off; the result says in
    `auto_off_before` whether it was on, so stop() can restore it."""
    return _switch("start", ssid, password, band if ssid else "", "on" if keep_on else "")


def stop(restore_auto_off: bool = False) -> dict:
    """Switch the hotspot off; `restore_auto_off` switches Windows' automatic turn-off on again (as before start)."""
    return _switch("stop", keep="restore" if restore_auto_off else "")


CAPABILITY_TEXT = {
    "Enabled": "possible",
    "DisabledByGroupPolicy": "blocked by a group policy (IT)",
    "DisabledByHardwareLimitation": "not supported by the Wi-Fi hardware / driver",
    "DisabledByOperator": "blocked by the mobile operator",
    "DisabledBySku": "not available in this Windows edition",
    "DisabledByRequiredAppNotInstalled": "a required app is missing",
    "DisabledDueToUnknownCause": "blocked for an unknown reason",
    "DisabledBySystemCapability": "blocked by a system setting",
    "NoConnectionToShare": "no active WLAN / LAN connection to share",
}


def summary(r: dict) -> list[str]:
    """Readable lines for the launcher log / card."""
    if not r.get("ok") and not r.get("capability"):
        return [f"[ERROR] {r.get('error', 'unknown error')}"]
    out = []
    if "wifi_adapter" in r:
        out.append(f"Wi-Fi adapter: {r['wifi_adapter'] or '(none found)'} {('- ' + r['wifi_status']) if r.get('wifi_status') else ''}".rstrip())
        out.append(f"Wi-Fi Direct adapters: {r.get('wifi_direct', 0)}  ·  domain: {r.get('domain') or 'none (workgroup)'}"
                   f"  ·  policies: {r.get('policies') or 'none set'}")
        cap = r.get("capability", "")
        out.append(f"Hotspot: {CAPABILITY_TEXT.get(cap, cap)}  ·  shared connection: {r.get('shared_connection') or '-'}")
    if r.get("state"):
        band = {"TwoPointFourGigahertz": "2.4 GHz", "FiveGigahertz": "5 GHz", "Auto": "auto"}.get(r.get("band", ""), r.get("band", ""))
        out.append(f"State: {r['state']}  ·  Wi-Fi name (SSID): {r.get('ssid', '')}  ·  password: {r.get('password', '')}")
        out.append(f"Security: {r.get('security') or '-'}  ·  band: {band or '-'}  ·  clients: {r.get('clients', 0)} of "
                   f"{r.get('max_clients', 8)}  ·  address: {r.get('ip') or '-'}  ·  Windows turns it off without devices: "
                   f"{'yes (after ~5 min)' if r.get('auto_off') else 'no' if r.get('auto_off') is False else '?'}")
    if r.get("error"):
        out.append(f"[ERROR] {r['error']}")
    return out
