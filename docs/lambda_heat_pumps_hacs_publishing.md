# Publishing Lambda Heat Pumps to HACS

This guide explains the process of publishing the Lambda Heat Pumps integration to the Home Assistant Community Store (HACS).

## 1. Prerequisites

Before submitting for inclusion in HACS default repository:

- [ ] GitHub account with public repository for the integration
- [ ] Integration that meets all HACS requirements
- [ ] Complete documentation
- [ ] Working code with tests

## 2. File Requirements

Ensure your repository has all the required files:

### Required Files for HACS

| File | Purpose |
|------|---------|
| `README.md` | Main repository documentation |
| `info.md` | Info displayed in HACS (can use README if `render_readme` is true) |
| `hacs.json` | HACS configuration file |

### Required Files for the Integration

| File | Purpose |
|------|---------|
| `custom_components/lambda_heat_pumps/manifest.json` | Integration manifest |
| `custom_components/lambda_heat_pumps/__init__.py` | Integration initialization |
| `custom_components/lambda_heat_pumps/config_flow.py` | Config flow support |
| License file (e.g., `LICENSE`) | Open source license |
| `/docs/*.md` | Documentation files |

## 3. Preparing the hacs.json File

The `hacs.json` file should include:

```json
{
    "name": "Lambda Heat Pumps",
    "render_readme": true,
    "content_in_root": false,
    "country": "DE",
    "homeassistant": "2024.4.4",
    "iot_class": "local_polling",
    "domains": ["climate", "sensor"],
    "zip_release": false,
    "filename": "lambda_heat_pumps.zip"
}
```

## 4. Preparing the manifest.json File

Ensure your `manifest.json` file is complete:

```json
{
  "domain": "lambda_heat_pumps",
  "name": "Lambda Heat Pumps",
  "version": "1.0.0",
  "config_flow": true,
  "documentation": "https://github.com/GuidoJeuken-6512/lambda_heat_pumps_hacs",
  "issue_tracker": "https://github.com/GuidoJeuken-6512/lambda_heat_pumps_hacs/issues",
  "requirements": ["pymodbus==3.6.1"],
  "dependencies": [],
  "after_dependencies": ["modbus"],
  "codeowners": ["@GuidoJeuken-6512"],
  "iot_class": "local_polling",
  "min_ha_version": "2024.4.4"
}
```

## 5. Set Up GitHub Repository

1. Create a public GitHub repository:
   - Name: `lambda_heat_pumps_hacs`
   - Description: "Lambda Heat Pumps integration for Home Assistant"
   - Public visibility

2. Initialize the repository with:
   - README.md
   - LICENSE (MIT recommended)
   - .gitignore (Python template)

3. Upload the integration code:
   ```bash
   git clone https://github.com/YOUR_USERNAME/lambda_heat_pumps_hacs.git
   cd lambda_heat_pumps_hacs
   # Copy all files to the repository
   git add .
   git commit -m "Initial commit"
   git push
   ```

## 6. Create Releases

1. Create a GitHub release:
   - Go to Releases > "Create a new release"
   - Tag version: `v1.0.0`
   - Title: "Initial Release"
   - Description: Include release notes
   - Publish release

## 7. HACS Validation

1. Set up the HACS validation action:
   - Create a file at `.github/workflows/validate.yml`
   - Add the following content:

```yaml
name: HACS Validation

on:
  push:
  pull_request:
  schedule:
    - cron: "0 0 * * *"

jobs:
  validate:
    runs-on: "ubuntu-latest"
    steps:
      - uses: "actions/checkout@v3"
      - name: HACS validation
        uses: "hacs/action@main"
        with:
          category: "integration"
```

2. Push this file to your repository:
   ```bash
   git add .github/workflows/validate.yml
   git commit -m "Add HACS validation workflow"
   git push
   ```

3. Check that the validation passes in the Actions tab of your GitHub repository.

## 8. Submit to HACS

1. Fork the [HACS default repository](https://github.com/hacs/default)
2. Add your integration to the `integration` file alphabetically:
   ```
   ...
   lambda_heat_pumps
   ...
   ```
3. Create a PR with the following information:
   - Title: "Add lambda_heat_pumps"
   - Body:
     ```
     - Integration name: Lambda Heat Pumps
     - Integration repository: https://github.com/YOUR_USERNAME/lambda_heat_pumps_hacs
     - GitHub username: YOUR_USERNAME
     - Integration category: integration
     ```

4. Wait for the HACS team to review your submission.

## 9. After Approval

Once approved:

1. Update your documentation to mention the official HACS support
2. Remove instructions about adding as a custom repository
3. Celebrate! 🎉

## 10. Maintaining

For future updates:

1. Make changes to your code
2. Update the version number in `manifest.json`
3. Create a new GitHub release with the updated version
4. Users can then update through HACS
