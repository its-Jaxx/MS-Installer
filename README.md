## MS Installer
<br>

- A Python application for generating application installer using either Winget or Chocolatey as package managers.
- Supports generating installers in Python, PowerShell, and Batch script formats.

---

<details>
<summary>Versions</summary>

<details>
<summary>Version 5 (July 13, 2025)</summary>

- Made everything `concurrent` yet again
- Added `caching` to load things way faster if already downloaded
- Auto install changed to accomodate for `urllib3`
- Added `icon.ico`
- Made it thread safely
- Added easy-to-understand error messages
- Added checks for SSL certificate
- Ensured order in `apps` and `category` dictionary
- Added retries to fetching
- Changed how `.json` files were parsed
</details>

<details>
<summary>Version 4 (July 12, 2025)</summary>

- Removed use of `asyncio` and `aiohttp`
- Made changes to the execution flow
</details>

<details>
<summary>Version 3 (July 12, 2025)</summary>

- Modified `Show Selected Apps` to allow searching within only selected apps
</details>

<details>
<summary>Version 2 (July 11, 2025)</summary>

- Added `async` to speed up booting time
- Added `Show Selected Apps` button to easily view all selected apps
</details>

<details>
<summary>Version 1 (July 10, 2025)</summary>

- Basic search functions
- Basic GUI look
- Supports `Python`, `PowerShell` and `Batch`
- Supports `Winget` and `Chocolatey`
</details>

</details>

---

<details>
<summary>Features (Detailed)</summary>

- Ability to select multiple applications to generate installers for
- Choose package manager:

    Winget | Chocolatey
    --- | ---

- Choose output installer script format:

    Script format | Extension
    |:---:|:---:|
    `Python` | `.py`
    `PowerShell` | `.ps1`
    `Batch` | `.bat`

- Quick search filter
- Descriptive tooltips for each application
- Double buffering - though very poorly done since it's not native to `tkinter`
- Automatic `Admin` elevation contained in each installer script
</details>

---

<details>
<summary>Requirements</summary>

- Python 3.x
- `Windows OS`
</details>

---

<details>
<summary>Usage</summary>

```bash
python "MS Installer.py"
```

- Use the left panel to select `Package Manager` and `Installer Format`.

- Search and select applications from the right panel.

- Click `Generate Installer` to create the installer script in the root directory.

- Use `Clear Selection` to reset chosen apps.

- `About` button to get to the `README.md` file.
</details>

---
