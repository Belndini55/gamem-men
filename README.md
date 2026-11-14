# 🎮 GameMen — Menedżer gier dla Windows

**GameMen** zbiera wszystkie Twoje gry w jednym miejscu — jak Lutris na Linuxie, ale pod Windows.
Skanuje dyski w poszukiwaniu gier z **Steam, Epic Games, GOG, Xbox / Game Pass, Battle.net, EA App, Ubisoft Connect, Riot Games i Minecraft**, a następnie pokazuje je w jednej, wygodnej bibliotece z okładkami, wyszukiwarką i przyciskiem **GRAJ**.

![platforms](https://img.shields.io/badge/platform-Windows-0078d4?style=flat-square) ![python](https://img.shields.io/badge/python-3.9%2B-blue?style=flat-square) ![deps](https://img.shields.io/badge/zależności-0%20(biblioteka%20standardowa)-success?style=flat-square)

---

## ✨ Co potrafi

| Funkcja | Opis |
|---|---|
| 🔍 **Skanowanie wszystkich launcherów** | Steam (wszystkie biblioteki dysków), Epic, GOG, Xbox/Game Pass, Battle.net, EA, Ubisoft, Riot, Minecraft |
| 🗂 **Rejestr Windows** | Wyłapuje też gry spoza głównych launcherów (Rockstar, Bethesda, gry DRM-free…) |
| 📂 **Własne foldery** | Możesz dodać dowolne foldery (np. `D:\Games`) w ustawieniach |
| 🖼 **Okładki gier** | Automatyczne okładki ze Steama, kolorowe placeholdery dla reszty |
| ▶️ **Uruchamianie** | Jeden przycisk GRAJ — przez URI launchera (`steam://…`) albo plik exe |
| ⭐ **Ulubione** | Oznaczaj gry gwiazdką |
| 🔎 **Szukaj / sortuj / filtruj** | Po nazwie, platformie, rozmiarze, dacie instalacji |
| 📊 **Statystyki** | Liczba gier, łączny rozmiar, największa gra |
| 🗑 **Deinstalacja** | Szybki dostęp do deinstalatora gry |
| 🌙 **Ciemny motyw** | Nowoczesny interfejs w stylu GOG Galaxy / Lutris |

**Zero zależności** — działa na czystej instalacji Pythona. Nic nie instalujesz przez pip.

---

## 🚀 Szybki start (Windows)

1. Zainstaluj [Python 3.9+](https://python.org) (zaznacz *„Add Python to PATH”* w instalatorze).
2. Pobierz ten projekt i wejdź do folderu.
3. Uruchom:

```bat
python app.py
```

4. W przeglądarce otworzy się `http://127.0.0.1:8765` z Twoją biblioteką gier.

Możesz też po prostu **kliknąć dwukrotnie `run.bat`**.

### Opcje wiersza poleceń

```bat
python app.py --port 9000      # inny port
python app.py --demo           # tryb demo z przykładowymi grami
python app.py --rescan         # wymuś świeże skanowanie
python app.py --no-browser     # nie otwieraj przeglądarki automatycznie
python app.py --verbose        # szczegółowe logi skanowania
```

---

## 🖥 Jak to działa

```
app.py                  → serwer WWW + API (biblioteka standardowa Pythona)
gamem/scanners/         → skanery poszczególnych launcherów:
    steam.py            → libraryfolders.vdf + appmanifest_*.acf (wszystkie biblioteki)
    epic.py             → manifesty .item z Epic Games Launcher (+ Legendary/Heroic)
    gog.py              → pliki goggame-*.info
    xbox.py             → C:\XboxGames + .gamingroot + AUMID z Get-StartApps
    battlenet.py        → Battle.net\Games + URI battlenet://
    ea.py               → EA Games / Origin Games + installerdata.xml
    ubisoft.py          → Ubisoft Game Launcher\games
    riot.py             → Riot Games (LoL, VALORANT…)
    minecraft.py        → %APPDATA%\.minecraft
    registry.py         → klucze Uninstall w rejestrze Windows
    folders.py          → własne foldery użytkownika
web/                    → interfejs (HTML/CSS/JS, bez frameworków)
```

Skanery nie ingerują w pliki launcherów — wszystko jest **tylko do odczytu**.
Ustawienia (ulubione, dodatkowe foldery) zapisują się w `%APPDATA%\GameMen\config.json`.

---

## 📦 Budowanie pliku .exe (opcjonalnie)

Jeśli chcesz samodzielny plik wykonywalny bez Pythona w PATH:

```bat
pip install pyinstaller
build_exe.bat
```

Powstały plik znajdziesz w folderze `dist\GameMen\`.

---

## ❓ FAQ

**Czy GameMen modyfikuje pliki gier albo launcherów?**
Nie. Odczytuje tylko pliki konfiguracyjne i katalogi w poszukiwaniu zainstalowanych gier.

**Dlaczego widzę tryb demo?**
Tryb włącza się automatycznie, gdy nie znaleziono żadnych gier (np. uruchomiono aplikację poza Windows). Użyj `python app.py --demo` żeby zobaczyć interfejs z przykładową biblioteką.

**Gra nie chce się uruchomić z poziomu GameMen.**
Niektóre tytuły wymagają aktywnego klienta launchera (np. gry UWP z Game Pass). Uruchom wtedy grę bezpośrednio z launchera i zgłoś problem.

**Czy aplikacja łączy się z internetem?**
Tylko przeglądarka — po okładki gier ze Steama (CDN). Sam skaner działa w pełni offline.

---

## 📄 Licencja

MIT — rób z tym co chcesz. Miłego grania! 🕹
