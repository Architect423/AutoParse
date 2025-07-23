from PIL import Image, ImageDraw

# Create a simple icon for the application
def create_icon():
    # Create a 256x256 image with transparent background
    size = 256
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Draw a simple camera/capture icon
    # Outer rectangle (camera body)
    margin = 40
    draw.rectangle([margin, margin+20, size-margin, size-margin], 
                   fill=(70, 130, 180, 255), outline=(50, 100, 150, 255), width=4)
    
    # Camera lens (circle)
    center = size // 2
    radius = 60
    draw.ellipse([center-radius, center-radius+10, center+radius, center+radius+10], 
                 fill=(240, 240, 240, 255), outline=(200, 200, 200, 255), width=3)
    
    # Inner lens
    inner_radius = 35
    draw.ellipse([center-inner_radius, center-inner_radius+10, center+inner_radius, center+inner_radius+10], 
                 fill=(50, 50, 50, 255))
    
    # Flash/viewfinder
    draw.rectangle([center-15, margin+5, center+15, margin+15], 
                   fill=(255, 255, 255, 255))
    
    # Save as ICO file
    img.save('icon.ico', format='ICO', sizes=[(256, 256), (128, 128), (64, 64), (32, 32), (16, 16)])
    print("Icon created: icon.ico")

if __name__ == "__main__":
    create_icon()
