"""Schreibt die Versionsinformationen (Eigenschaften > Details) der EXE: ``make_version_info.py <Version> <Zieldatei>``."""
import sys

version, target = sys.argv[1], sys.argv[2]
parts = (version.split(".") + ["0"] * 4)[:4]
numbers = tuple(int(p) if p.isdigit() else 0 for p in parts)
text = f"""VSVersionInfo(
  ffi=FixedFileInfo(filevers={numbers}, prodvers={numbers}, mask=0x3f, flags=0x0, OS=0x40004, fileType=0x1, subtype=0x0, date=(0, 0)),
  kids=[
    StringFileInfo([StringTable('040704B0', [
      StringStruct('CompanyName', 'TBK'),
      StringStruct('FileDescription', 'P3D PDF Reader'),
      StringStruct('FileVersion', '{version}'),
      StringStruct('InternalName', 'P3D_PDF_Reader'),
      StringStruct('OriginalFilename', 'P3D_PDF_Reader.exe'),
      StringStruct('ProductName', 'P3D PDF Reader'),
      StringStruct('ProductVersion', '{version}')])]),
    VarFileInfo([VarStruct('Translation', [1031, 1200])])])
"""
open(target, "w", encoding="utf-8").write(text)
