# R-OSSE Header Image Specifications

## Image Requirements

- **Filename**: `rosse-header.png`
- **Dimensions**: 
  - **Recommended**: 1920x120 pixels (wide format for desktop displays)
  - **Minimum**: 800x120 pixels
  - **Safe area**: Center 800x120px will always be visible on all screens
  - **Outer areas**: Will crop on mobile/narrower screens

## Design Guidelines

- **Theme**: Retro terminal/CRT aesthetic with green phosphor colors
- **Background**: Black (#000000) or very dark green
- **Text/Graphics**: Bright green (#00FF00) with optional glow effects
- **Style**: Should complement the terminal UI aesthetic of the application
- **Content**: R-OSSE Horn Profile Explorer branding

## Safe Area Layout

```
|<----- Crop Area ----->|<----- Safe Area (800x120) ----->|<----- Crop Area ----->|
|                       |  Always visible on all devices  |                       |
|   Decorative only     |    Critical text and logos      |   Decorative only     |
|                       |                                 |                       |
```

## Fallback Behavior

If the image fails to load or doesn't exist, the page will automatically display:
- Title: "▓▒░ R-OSSE HORN PROFILE EXPLORER ░▒▓"
- Subtitle: "INTERACTIVE ACOUSTIC HORN GEOMETRY OPTIMIZATION SYSTEM v1.0"

This provides a seamless experience even without a custom header image.

## Example Color Scheme

- Primary: #00FF00 (bright green)
- Secondary: #00AA00 (medium green)
- Tertiary: #003300 (dark green)
- Background: #000000 (black)
- Effects: Scanlines, CRT glow, phosphor blur

## Creating the Image

1. Create a 1920x120px image in your favorite graphics editor
2. Use the terminal color scheme specified above
3. Place critical elements in the center 800px
4. Add decorative elements in the outer areas (optional)
5. Export as PNG with transparency if desired
6. Save as `rosse-header.png` in this directory
