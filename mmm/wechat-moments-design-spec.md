# WeChat Moments (微信朋友圈) UI Design Specification

## 1. Top Navigation Bar

### Dimensions
- **Height**: 55-64px (varies by platform)
  - iOS: 44px content + 20px status bar = 64px total
  - Android: 56px
- **Safe area**: Respects device notch/status bar

### Background
- **Default state**: Transparent (`Colors.transparent`)
- **Scrolled state**: `#EDEDED` (RGB: 237, 237, 237) with opacity animation
  - Opacity transitions from 0 to 1 as user scrolls past 200px
  - Full opacity reached at 300px scroll offset

### Text & Icons
- **Title "朋友圈"**:
  - Font size: 17-18px
  - Font weight: 500-700
  - Color: White (default) / Black (when scrolled)
  - Alignment: Center
- **Back button (←)**:
  - Position: Left side
  - Icon size: 24px
  - Color: White (default) / Black (when scrolled)
  - Margin: 8px
- **Camera icon**:
  - Position: Right side
  - Icon: `camera_alt_outlined` / Camera icon
  - Size: 24px
  - Color: White (default) / Black (when scrolled)
  - Margin: 8px

---

## 2. Cover Photo Area (个人主页封面)

### Dimensions
- **Height**: `screen_width × 0.75` (3:4 aspect ratio)
  - iPhone 14 (390px): ~293px height
  - iPhone 14 Pro Max (430px): ~323px height
- **Width**: Full screen width
- **Corner radius**: 30px (continuous style)
- **Background**: User-uploaded cover image

### Avatar Position
- **Position**: Bottom-right corner
- **Offset from right edge**: 18-20px
- **Offset from bottom**: 10-20px
- **Size**: 68-80px (width × height)
- **Shape**: Circle / Rounded rectangle (border-radius: 12px in some implementations)
- **Border**: None (clean look)
- **Shadow**: 
  - Color: `primary.opacity(0.15)`
  - Radius: 5px
  - Offset: (0, 2)

### Username Position
- **Position**: Left of avatar, vertically centered
- **Offset from avatar**: 8-10px
- **Font size**: 18px
- **Font weight**: 500 (medium)
- **Color**: White (`#FFFFFF`)
- **Letter spacing**: 2px
- **Line height**: 2.5

---

## 3. Post Card Layout (朋友圈动态卡片)

### Card Structure
- **Background**: Semi-transparent material (`thinMaterial`)
- **Corner radius**: 30px (continuous style)
- **Shadow**:
  - Color: `black.opacity(0.15)`
  - Radius: 20px
  - Offset: (0, 20)
- **Horizontal padding**: 18px from screen edges
- **Vertical padding**: 18px between cards

### Avatar Section
- **Size**: 44-48px (width × height)
- **Shape**: Circle
- **Position**: Top-left of card
- **Left padding**: 18px
- **Top padding**: 18px
- **Shadow**:
  - Color: `primary.opacity(0.15)`
  - Radius: 5px
  - Offset: (0, 2)

### Content Area (Right of Avatar)
- **Left spacing from avatar**: 8-18px
- **Right padding**: 18px

### Username
- **Font size**: 16-18px
- **Font weight**: Bold (700)
- **Color**: 
  - Light mode: `#174B73` (RGB: 23, 75, 115) - "textEmphasizeColor"
  - Dark mode: `#000000`

### Post Text Content
- **Font size**: 16px
- **Color**: Black (`#000000`) / `Colors.black87`
- **Max lines**: 8 (text-only posts), 3 (posts with images)
- **Line height**: 1.5

### Location Text
- **Font size**: 14px
- **Color**: `Colors.black54` / Gray

### Timestamp
- **Font size**: 14px
- **Color**: Secondary color / Gray
- **Position**: Below content, left-aligned

### "More" Button (⋯)
- **Position**: Right side, same row as timestamp
- **Background**: `Colors.grey[200]` / `#F5F5F5`
- **Icon**: `more_horiz_outlined`
- **Size**: 24px
- **Padding**: 2px horizontal
- **Border radius**: 4px

---

## 4. Like/Comment Section (点赞评论区域)

### Container
- **Background**: `Colors.grey[100]` / `#F5F5F5`
- **Padding**: 10px (all sides)
- **Position**: Below main content

### Like Section
- **Icon**: 
  - `favorite_border_outlined` (empty heart) / `heart`
  - Size: 20px
  - Color: `textEmphasizeColor` (`#174B73`) / Secondary color
- **Like avatars**:
  - Size: 20-30px
  - Shape: Circle
  - Spacing: 5px between avatars
  - Shadow:
    - Color: `primary.opacity(0.15)`
    - Radius: 3px
    - Offset: (0, 2)

### Comment Section
- **Icon**:
  - `chat_bubble_outline` / Comment icon
  - Size: 20px
  - Color: `textEmphasizeColor` (`#174B73`)
- **Comment layout**:
  - Avatar: 30px × 30px
  - Username font: 14px, weight 500, color `textEmphasizeColor`
  - Timestamp: 14px, color grey
  - Content: 16px, default text color
  - Spacing between comments: 10px

### Like/Comment Action Menu (Popup)
- **Background**: `Colors.black87` / `#CC000000` (80% black)
- **Border radius**: 4px
- **Animation**: Slide from right, 100ms duration
- **Buttons**:
  - "点赞" (Like): Heart icon + text
  - "评论" (Comment): Chat bubble icon + text
  - Icon color: White
  - Text color: White
  - Font weight: w400
  - Spacing: Even distribution

---

## 5. Image Grid Layout (九宫格图片)

### Grid Configuration
- **Columns**: 3 (fixed)
- **Spacing**: 4px (horizontal and vertical)
- **Max images**: 9

### Image Sizing by Count

| Image Count | Layout | Single Image Width |
|-------------|--------|-------------------|
| 1 | Single large | `container_width × 0.7` |
| 2 | 1×2 grid | `(container_width - 8px) / 3` |
| 3 | 1×3 grid | `(container_width - 8px) / 3` |
| 4 | 2×2 grid | `(container_width - 8px) / 3` |
| 5 | 2×3 grid (2+3) | `(container_width - 8px) / 3` |
| 6 | 2×3 grid (3+3) | `(container_width - 8px) / 3` |
| 7 | 3×3 grid (3+3+1) | `(container_width - 8px) / 3` |
| 8 | 3×3 grid (3+3+2) | `(container_width - 8px) / 3` |
| 9 | 3×3 grid (3+3+3) | `(container_width - 8px) / 3` |

### Image Properties
- **Aspect ratio**: 1:1 (square)
- **Fit mode**: `cover` (crop to fill)
- **Border radius**: 4-8px
- **Background**: Placeholder / Loading spinner

### Video Post
- **Thumbnail width**: `container_width × 0.7`
- **Aspect ratio**: 1:1 (square thumbnail)
- **Play button**: 
  - Icon: `play_circle_fill_outlined`
  - Color: White
  - Size: 32px
  - Position: Center of thumbnail

---

## 6. Action Buttons (操作按钮)

### Like Toggle Button
- **Position**: Bottom-right of post card
- **Size**: 44px × 44px (touch target)
- **Icon**: `heart.fill`
- **Icon size**: 24px
- **States**:
  - Not liked: `likeButtonNotSelected` (`#E1E1EB` / RGB: 225, 225, 235)
  - Liked: `likeButtonSelected` (`#F73757` / RGB: 247, 55, 87)
- **Background**: Gradient circle
  - Start: `likeButtonFillStart` (lighter)
  - End: `likeButtonFillEnd` (darker)
- **Shadow**:
  - Light: `likeButtonStart` color, 5px radius
  - Dark: `likeButtonEnd` color, 5px radius
- **Animation**: Scale/press effect

### Comment Button
- **Icon**: `chat_bubble_outline`
- **Size**: 24px
- **Color**: Secondary/Gray

### Camera Button (in Nav Bar)
- **Icon**: `camera_alt_outlined`
- **Size**: 24px
- **Color**: White (default) / Black (scrolled)

---

## 7. Overall Color Scheme (整体配色方案)

### Primary Colors

| Color Name | Hex | RGB | Usage |
|------------|-----|-----|-------|
| Background | `#D6D7E3` | 214, 215, 227 | Page background (light) |
| Background Dark | `#111111` | 17, 17, 17 | Page background (dark) |
| Primary Text | `#181818` | 24, 24, 24 | Main text (light mode) |
| Primary Text Dark | `#000000` | 0, 0, 0 | Main text (dark mode) |
| Secondary Text | `#333333` | 51, 51, 51 | Secondary text (light) |
| Secondary Text Dark | `#CCCCCC` | 204, 204, 204 | Secondary text (dark) |
| Text Emphasize | `#174B73` | 23, 75, 115 | Usernames, links |
| App Bar Scrolled | `#EDEDED` | 237, 237, 237 | Nav bar background |

### Like Button Colors

| Color Name | Hex | RGB | Usage |
|------------|-----|-----|-------|
| Not Selected | `#E1E1EB` | 225, 225, 235 | Unfilled heart |
| Selected | `#F73757` | 247, 55, 87 | Filled heart |
| Fill Start | Light gradient | - | Button gradient start |
| Fill End | Dark gradient | - | Button gradient end |
| Shadow Start | Light | - | Neumorphism light |
| Shadow End | Dark | - | Neumorphism dark |

### UI Element Colors

| Element | Light Mode | Dark Mode |
|---------|------------|-----------|
| Card Background | `thinMaterial` | `thinMaterial` |
| Like/Comment BG | `#F5F5F5` | `#1A1A1A` |
| Divider | `#E0E0E0` | `#333333` |
| Icon Default | `#666666` | `#999999` |
| Placeholder | `#F0F0F0` | `#2A2A2A` |

### Accent Colors

| Color | Hex | Usage |
|-------|-----|-------|
| Accent | `#FFD700` | Highlights, badges |
| Link Blue | `#576B95` | Clickable text |
| Error Red | `#FA5151` | Errors, alerts |
| Success Green | `#07C160` | Success states |

---

## 8. Typography (字体规范)

### Font Family
- **iOS**: -apple-system, SF Pro Text, SF Pro Display
- **Android**: Roboto, Noto Sans CJK SC
- **Fallback**: PingFang SC, Microsoft YaHei, sans-serif

### Font Sizes

| Element | Size | Weight | Line Height |
|---------|------|--------|-------------|
| Nav Title | 17-18px | 500-700 | 1.4 |
| Username (Post) | 16-18px | 700 (Bold) | 1.5 |
| Post Content | 16px | 400 (Regular) | 1.5 |
| Location | 14px | 400 | 1.4 |
| Timestamp | 14px | 400 | 1.4 |
| Comment Username | 14px | 500 | 1.4 |
| Comment Content | 16px | 400 | 1.5 |
| Button Text | 16px | 400-500 | 1.4 |

---

## 9. Spacing & Layout Constants (间距与布局)

### Global Spacing
- **Page padding**: 12-18px
- **Card padding**: 18px (all sides)
- **Card margin**: 18px horizontal
- **Card gap**: 18-20px vertical
- **Content spacing**: 10px (between elements)
- **Image grid spacing**: 4px
- **Avatar to content**: 8-18px

### Border Radius
- **Cards**: 30px (continuous)
- **Avatars**: 50% (circle) or 12px (rounded)
- **Images**: 4-8px
- **Buttons**: 4-8px
- **Input fields**: 10px

### Shadows
- **Card shadow**: 
  - Color: `black.opacity(0.15)`
  - Radius: 20px
  - Offset: (0, 20)
- **Avatar shadow**:
  - Color: `primary.opacity(0.15)`
  - Radius: 5px
  - Offset: (0, 2)

---

## 10. Animations (动画规范)

### Scroll-based
- **Nav bar opacity**: 300ms ease-in-out
- **Parallax effect**: Cover image moves at 0.05× scroll speed

### Interactions
- **Like button**: 100ms scale animation
- **Action menu**: 100ms slide-in from right
- **Card press**: 200ms scale down to 0.9
- **Page transitions**: 300ms fade

### Loading
- **Skeleton screen**: Shimmer animation
- **Image loading**: Progress spinner

---

## 11. Responsive Breakpoints (响应式断点)

| Device | Width | Columns | Image Size |
|--------|-------|---------|------------|
| iPhone SE | 375px | 3 | ~110px |
| iPhone 14 | 390px | 3 | ~115px |
| iPhone 14 Pro | 393px | 3 | ~116px |
| iPhone 14 Pro Max | 430px | 3 | ~128px |
| iPad | 768px | 3 | ~230px |
| iPad Pro | 1024px | 3 | ~310px |

---

## 12. Dark Mode Support (深色模式)

### Color Mapping
| Element | Light | Dark |
|---------|-------|------|
| Background | `#D6D7E3` | `#111111` |
| Card BG | Material | Material |
| Text Primary | `#181818` | `#FFFFFF` |
| Text Secondary | `#333333` | `#CCCCCC` |
| Divider | `#E0E0E0` | `#333333` |
| Icon | `#666666` | `#999999` |

### Implementation Notes
- Use `@Environment(\.colorScheme)` in SwiftUI
- Use `Theme.of(context).brightness` in Flutter
- Use `prefers-color-scheme` media query in CSS

---

*Document compiled from analysis of multiple WeChat Moments implementations including SwiftUI, Flutter, and React Native projects.*