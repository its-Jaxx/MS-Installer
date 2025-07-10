## MS Installer
<br>

- A Python application for generating application installer using either Winget or Chocolatey as package managers.
- Supports generating installers in Python, PowerShell, and Batch script formats.

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
