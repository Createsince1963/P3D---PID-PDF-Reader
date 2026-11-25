"""Zeichen im Tag ersetzen (Ansicht, ohne Qt): der Nutzer ersetzt ein Zeichen (oder eine Zeichenfolge) im Tag durch ein
Zeichen seiner Wahl, auch durch nichts (z. B. ``-`` -> leer: XV-130 -> XV130).

Das Original bleibt unveraendert (PDF, Review-Speicher); die Regel wirkt auf den angezeigten und exportierten Tag, auf die
Projekt-Pruefung (``Checker.check``) und den Abgleich mit der Importliste. Eine Regel fuer alle Tags."""
from __future__ import annotations


class TagEdit:
    def __init__(self) -> None:
        self.find, self.to = "", ""

    @property
    def active(self) -> bool:
        return bool(self.find)

    @staticmethod
    def problem(find: str, to: str) -> str:
        """Hinweistext, wenn die Regel unzulaessig ist (leer = in Ordnung). Das Ersatzzeichen darf das Suchzeichen nicht
        enthalten, sonst waere das Ergebnis vom mehrfachen Anwenden abhaengig."""
        if not find:
            return "Bitte ein Zeichen zum Ersetzen angeben."
        if find in to:
            return "Das Ersatzzeichen darf das gesuchte Zeichen nicht enthalten."
        return ""

    def set(self, find: str, to: str) -> None:
        err = self.problem(find, to)
        if err and find:
            raise ValueError(err)
        self.find, self.to = (find, to) if find else ("", "")

    def clear(self) -> None:
        self.find, self.to = "", ""

    def apply(self, tag):
        return tag.replace(self.find, self.to) if self.find and isinstance(tag, str) else tag

    def describe(self) -> str:
        return f"„{self.find}“ → „{self.to}“" if self.find else ""


RULE = TagEdit()


def apply(tag):
    """Tag mit der aktuellen Ersetzungsregel (ohne Regel unveraendert)."""
    return RULE.apply(tag)
