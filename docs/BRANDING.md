# Smart CLI Branding Guide

<div align="center">
  <img src="https://raw.githubusercontent.com/raufA1/smart-cli/main/smart-cli-logo/icons/icon-512.png" alt="Smart CLI Logo" width="256" height="256">
</div>

## Logo Usage

### Available Assets

| Size | File | Usage |
|------|------|-------|
| 16px | `smart-cli-logo/icons/icon-16.png` | Favicon, small UI elements |
| 20px | `smart-cli-logo/icons/icon-20.png` | Inline text icons, menu items |
| 24px | `smart-cli-logo/icons/icon-24.png` | Button icons, toolbar |
| 32px | `smart-cli-logo/icons/icon-32.png` | Section headers, medium UI |
| 256px | `smart-cli-logo/icons/icon-256.png` | Main logo display |
| 512px | `smart-cli-logo/icons/icon-512.png` | High-res displays, print |
| 1024px | `smart-cli-logo/icons/icon-1024.png` | App store, large displays |

### Vector Formats

| File | Usage |
|------|-------|
| `logo.svg` | Default version (dark on light) |
| `logo-light.svg` | Light version (for dark backgrounds) |
| `logo-dark.svg` | Dark version (enhanced contrast) |

### Usage Examples

#### README Header
```html
<div align="center">
  <img src="https://raw.githubusercontent.com/raufA1/smart-cli/main/smart-cli-logo/icons/icon-256.png" alt="Smart CLI Logo" width="128" height="128">
</div>
```

#### Inline Text Icons
```html
<img src="https://raw.githubusercontent.com/raufA1/smart-cli/main/smart-cli-logo/icons/icon-20.png" alt="Smart CLI" width="16" height="16" style="vertical-align: middle;"> **Command Examples**
```

#### Section Headers
```html
<img src="https://raw.githubusercontent.com/raufA1/smart-cli/main/smart-cli-logo/icons/icon-32.png" alt="Smart CLI" width="24" height="24" style="vertical-align: middle;"> **Get started with Smart CLI**
```

## Brand Guidelines

### Colors
- Primary: Terminal blue (#0066CC)
- Secondary: Terminal green (#00AA00)
- Background: Terminal black (#000000)
- Text: Terminal white (#FFFFFF)

### Typography
- Monospace fonts preferred for technical content
- Clean, modern sans-serif for marketing content

### Voice & Tone
- **Professional** but **approachable**
- **Technical** but **clear**
- **Enterprise-focused** but **developer-friendly**

## File Structure

```
smart-cli-logo/
├── README.md              # Logo usage guide
├── logo.svg              # Default vector logo
├── logo-light.svg        # Light version for dark backgrounds  
├── logo-dark.svg         # Dark version with enhanced contrast
├── favicon.ico           # Web favicon
├── social-card.png       # Social media preview (1200×630)
└── icons/               # PNG icons in multiple sizes
    ├── icon-16.png      # 16×16 for favicons, small UI
    ├── icon-20.png      # 20×20 for inline text, menus
    ├── icon-24.png      # 24×24 for buttons, toolbar
    ├── icon-32.png      # 32×32 for section headers
    ├── icon-256.png     # 256×256 for main logo display
    ├── icon-512.png     # 512×512 for high-res displays
    └── icon-1024.png    # 1024×1024 for app stores
```

## Implementation Checklist

- [x] README header logo (256px → 128px display)
- [x] Section header icons (32px → 24px display)  
- [x] Inline text icons (20px → 16px display)
- [x] Favicon setup (favicon.ico)
- [x] Social preview card (social-card.png)
- [ ] GitHub repository social preview (manual setup required)
- [x] Documentation branding assets

---

© Smart CLI — Professional AI-Powered CLI Platform