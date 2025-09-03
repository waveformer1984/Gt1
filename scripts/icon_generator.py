#!/usr/bin/env python3
"""
🎨 Hydi Icon Generator
Create unified icons for desktop and mobile applications
"""

import os
import sys
from pathlib import Path
import json
import base64
from io import BytesIO

try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

class IconGenerator:
    """Generates icons for Hydi applications across platforms"""
    
    def __init__(self):
        self.script_dir = Path(__file__).parent
        self.project_root = self.script_dir.parent
        self.assets_dir = self.project_root / "assets" / "icons"
        self.assets_dir.mkdir(parents=True, exist_ok=True)
        
        # Icon specifications for different platforms
        self.icon_specs = {
            "desktop": {
                "windows": [16, 32, 48, 64, 128, 256],
                "macos": [16, 32, 64, 128, 256, 512, 1024],
                "linux": [16, 22, 24, 32, 48, 64, 128, 256, 512]
            },
            "mobile": {
                "android": {
                    "mdpi": 48, "hdpi": 72, "xhdpi": 96, "xxhdpi": 144, "xxxhdpi": 192,
                    "notification": [24, 36, 48, 72, 96],
                    "launcher": [48, 72, 96, 144, 192]
                },
                "ios": {
                    "app": [20, 29, 40, 58, 60, 76, 80, 87, 120, 152, 167, 180, 1024],
                    "notification": [20, 40, 60],
                    "settings": [29, 58, 87],
                    "spotlight": [40, 80, 120]
                }
            }
        }
    
    def create_base_icon(self, size=512):
        """Create the base Hydi icon design"""
        if not PIL_AVAILABLE:
            print("⚠️  PIL not available, creating placeholder icon")
            return self._create_placeholder_icon(size)
        
        # Create a new image with transparency
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Color scheme - Neural network inspired
        primary_color = (102, 51, 153)    # Purple
        secondary_color = (255, 102, 51)  # Orange
        accent_color = (51, 255, 153)     # Green
        
        # Draw main circle background
        margin = size // 10
        circle_bbox = [margin, margin, size - margin, size - margin]
        draw.ellipse(circle_bbox, fill=primary_color)
        
        # Draw neural network nodes
        node_size = size // 20
        nodes = [
            (size * 0.3, size * 0.3),
            (size * 0.7, size * 0.3),
            (size * 0.2, size * 0.5),
            (size * 0.8, size * 0.5),
            (size * 0.35, size * 0.7),
            (size * 0.65, size * 0.7),
            (size * 0.5, size * 0.85)
        ]
        
        # Draw connections between nodes
        connections = [
            (0, 2), (0, 4), (1, 3), (1, 5),
            (2, 4), (3, 5), (4, 6), (5, 6),
            (0, 1), (2, 3)
        ]
        
        for start, end in connections:
            x1, y1 = nodes[start]
            x2, y2 = nodes[end]
            draw.line([(x1, y1), (x2, y2)], fill=accent_color, width=max(2, size//100))
        
        # Draw nodes
        for x, y in nodes:
            node_bbox = [x - node_size, y - node_size, x + node_size, y + node_size]
            draw.ellipse(node_bbox, fill=secondary_color)
        
        # Add center "H" for Hydi
        try:
            # Try to use a built-in font
            font_size = size // 3
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            try:
                font = ImageFont.load_default()
            except:
                font = None
        
        if font:
            text = "H"
            # Get text bounding box
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            # Center the text
            x = (size - text_width) // 2
            y = (size - text_height) // 2 - size // 20
            
            # Draw text with outline
            outline_width = max(1, size // 200)
            for dx in range(-outline_width, outline_width + 1):
                for dy in range(-outline_width, outline_width + 1):
                    if dx != 0 or dy != 0:
                        draw.text((x + dx, y + dy), text, font=font, fill=(0, 0, 0))
            
            draw.text((x, y), text, font=font, fill=(255, 255, 255))
        
        return img
    
    def _create_placeholder_icon(self, size):
        """Create a simple placeholder icon without PIL"""
        # Create SVG content
        svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="{size}" height="{size}" viewBox="0 0 {size} {size}" xmlns="http://www.w3.org/2000/svg">
    <circle cx="{size//2}" cy="{size//2}" r="{size//2-10}" fill="#6633FF" stroke="#FF6633" stroke-width="4"/>
    <text x="{size//2}" y="{size//2+size//6}" text-anchor="middle" font-family="Arial, sans-serif" font-size="{size//3}" font-weight="bold" fill="white">H</text>
</svg>'''
        
        svg_path = self.assets_dir / f"hydi_icon_{size}.svg"
        with open(svg_path, 'w') as f:
            f.write(svg_content)
        
        return svg_path
    
    def generate_desktop_icons(self):
        """Generate desktop icons for all platforms"""
        print("🖥️  Generating desktop icons...")
        
        if PIL_AVAILABLE:
            base_icon = self.create_base_icon(1024)
            
            # Windows ICO file
            ico_sizes = self.icon_specs["desktop"]["windows"]
            ico_images = []
            for size in ico_sizes:
                resized = base_icon.resize((size, size), Image.Resampling.LANCZOS)
                ico_images.append(resized)
            
            ico_path = self.assets_dir / "hydi_icon.ico"
            ico_images[0].save(ico_path, format='ICO', sizes=[(img.width, img.height) for img in ico_images])
            print(f"✅ Created Windows ICO: {ico_path}")
            
            # macOS ICNS (save as PNG for now, requires iconutil for proper ICNS)
            for size in self.icon_specs["desktop"]["macos"]:
                resized = base_icon.resize((size, size), Image.Resampling.LANCZOS)
                png_path = self.assets_dir / f"hydi_icon_{size}.png"
                resized.save(png_path, format='PNG')
            
            print(f"✅ Created macOS PNG icons in {self.assets_dir}")
            
            # Linux PNG
            main_png = self.assets_dir / "hydi_icon.png"
            base_icon.resize((256, 256), Image.Resampling.LANCZOS).save(main_png, format='PNG')
            print(f"✅ Created Linux PNG: {main_png}")
            
        else:
            # Create SVG fallbacks
            for size in [16, 32, 48, 64, 128, 256, 512, 1024]:
                self._create_placeholder_icon(size)
            print(f"✅ Created SVG icons in {self.assets_dir}")
    
    def generate_mobile_icons(self):
        """Generate mobile app icons"""
        print("📱 Generating mobile icons...")
        
        # Android icons
        android_dir = self.assets_dir / "android"
        android_dir.mkdir(exist_ok=True)
        
        if PIL_AVAILABLE:
            base_icon = self.create_base_icon(1024)
            
            # Android launcher icons
            for density, size in self.icon_specs["mobile"]["android"].items():
                if isinstance(size, int):
                    density_dir = android_dir / f"mipmap-{density}"
                    density_dir.mkdir(exist_ok=True)
                    
                    resized = base_icon.resize((size, size), Image.Resampling.LANCZOS)
                    icon_path = density_dir / "ic_launcher.png"
                    resized.save(icon_path, format='PNG')
                    
                    # Also create round icon
                    round_icon = self._create_round_icon(resized)
                    round_path = density_dir / "ic_launcher_round.png"
                    round_icon.save(round_path, format='PNG')
            
            print(f"✅ Created Android icons in {android_dir}")
            
            # iOS icons
            ios_dir = self.assets_dir / "ios"
            ios_dir.mkdir(exist_ok=True)
            
            for size in self.icon_specs["mobile"]["ios"]["app"]:
                resized = base_icon.resize((size, size), Image.Resampling.LANCZOS)
                icon_path = ios_dir / f"icon_{size}x{size}.png"
                resized.save(icon_path, format='PNG')
            
            print(f"✅ Created iOS icons in {ios_dir}")
        
        else:
            print("⚠️  PIL not available, skipping mobile icon generation")
    
    def _create_round_icon(self, square_icon):
        """Create a round version of the icon for Android"""
        if not PIL_AVAILABLE:
            return None
        
        size = square_icon.size[0]
        mask = Image.new('L', (size, size), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.ellipse((0, 0, size, size), fill=255)
        
        round_icon = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        round_icon.paste(square_icon, (0, 0))
        round_icon.putalpha(mask)
        
        return round_icon
    
    def update_mobile_config(self):
        """Update mobile app configuration with new icons"""
        print("⚙️  Updating mobile app configuration...")
        
        # Update React Native app.json
        mobile_app_json = self.project_root / "mobile" / "hydi-mobile" / "app.json"
        if mobile_app_json.exists():
            with open(mobile_app_json, 'r') as f:
                config = json.load(f)
            
            # Add icon configuration
            config["expo"] = config.get("expo", {})
            config["expo"]["icon"] = "./assets/icons/hydi_icon.png"
            config["expo"]["splash"] = {
                "image": "./assets/icons/hydi_icon.png",
                "resizeMode": "contain",
                "backgroundColor": "#6633FF"
            }
            config["expo"]["android"] = config["expo"].get("android", {})
            config["expo"]["android"]["icon"] = "./assets/icons/android/mipmap-xxxhdpi/ic_launcher.png"
            config["expo"]["ios"] = config["expo"].get("ios", {})
            config["expo"]["ios"]["icon"] = "./assets/icons/ios/icon_1024x1024.png"
            
            with open(mobile_app_json, 'w') as f:
                json.dump(config, f, indent=2)
            
            print(f"✅ Updated {mobile_app_json}")
    
    def create_desktop_shortcuts(self):
        """Create desktop shortcuts with icons"""
        print("🔗 Creating desktop shortcuts...")
        
        desktop_path = Path.home() / "Desktop"
        if not desktop_path.exists():
            desktop_path = Path.home()  # Fallback
        
        # Windows shortcut
        if sys.platform == "win32":
            self._create_windows_shortcut(desktop_path)
        
        # Linux desktop file
        elif sys.platform.startswith("linux"):
            self._create_linux_desktop_file(desktop_path)
        
        # macOS app bundle (simplified)
        elif sys.platform == "darwin":
            self._create_macos_shortcut(desktop_path)
    
    def _create_windows_shortcut(self, desktop_path):
        """Create Windows shortcut"""
        try:
            import win32com.client
            
            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut_path = desktop_path / "Hydi AI.lnk"
            shortcut = shell.CreateShortCut(str(shortcut_path))
            shortcut.Targetpath = str(self.project_root / "scripts" / "hydi_startup.bat")
            shortcut.WorkingDirectory = str(self.project_root)
            shortcut.IconLocation = str(self.assets_dir / "hydi_icon.ico")
            shortcut.Description = "Hydi Advanced AI REPL & Automation Framework"
            shortcut.save()
            
            print(f"✅ Created Windows shortcut: {shortcut_path}")
            
        except ImportError:
            print("⚠️  pywin32 not available, skipping Windows shortcut")
    
    def _create_linux_desktop_file(self, desktop_path):
        """Create Linux .desktop file"""
        desktop_file_content = f"""[Desktop Entry]
Version=1.0
Type=Application
Name=Hydi AI
Comment=Advanced AI REPL & Automation Framework
Exec={self.project_root}/scripts/hydi_startup.sh
Icon={self.assets_dir}/hydi_icon.png
Terminal=false
StartupNotify=true
Categories=Development;Utility;
"""
        
        desktop_file = desktop_path / "Hydi AI.desktop"
        with open(desktop_file, 'w') as f:
            f.write(desktop_file_content)
        
        os.chmod(desktop_file, 0o755)
        print(f"✅ Created Linux desktop file: {desktop_file}")
    
    def _create_macos_shortcut(self, desktop_path):
        """Create macOS shortcut (simplified)"""
        # Create a simple shell script that can be double-clicked
        script_content = f"""#!/bin/bash
cd "{self.project_root}"
{self.project_root}/scripts/hydi_startup.sh
"""
        
        shortcut_path = desktop_path / "Hydi AI.command"
        with open(shortcut_path, 'w') as f:
            f.write(script_content)
        
        os.chmod(shortcut_path, 0o755)
        print(f"✅ Created macOS shortcut: {shortcut_path}")
    
    def generate_all_icons(self):
        """Generate all icons and configurations"""
        print("🎨 Hydi Icon Generator")
        print("=" * 40)
        
        if not PIL_AVAILABLE:
            print("⚠️  PIL/Pillow not installed. Installing fallback SVG icons.")
            print("   For better icons, install Pillow: pip install Pillow")
        
        self.generate_desktop_icons()
        self.generate_mobile_icons()
        self.update_mobile_config()
        self.create_desktop_shortcuts()
        
        print("\n🎉 Icon generation completed!")
        print(f"📁 Icons saved to: {self.assets_dir}")
        print("💡 Icons are now configured for desktop and mobile apps")

def main():
    """Main entry point"""
    generator = IconGenerator()
    generator.generate_all_icons()
    return 0

if __name__ == "__main__":
    sys.exit(main())