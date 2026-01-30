import urllib.request
import os

def download_images():
    if not os.path.exists('images'):
        os.makedirs('images')
        print("✅ Created 'images' folder")
    
    # Free food images from Unsplash
    images = {
        '1.jpg': 'https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=400',  # Burger
        '2.jpg': 'https://images.unsplash.com/photo-1509042239860-f550ce710b93?w=400',  # Coffee
        '3.jpg': 'https://images.unsplash.com/photo-1513104890138-7c749659a591?w=400',  # Pizza
        '4.jpg': 'https://images.unsplash.com/photo-1621996346565-e3dbc646d9a9?w=400',  # Pasta
        '5.jpg': 'https://images.unsplash.com/photo-1528735602780-2552fd46c7af?w=400',  # Sandwich
        '6.jpg': 'https://images.unsplash.com/photo-1573080496219-bb080dd4f877?w=400',  # Fries
        '7.jpg': 'https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=400',  # Salad
        '8.jpg': 'https://images.unsplash.com/photo-1563805042-7684c019e1cb?w=400',  # Ice Cream
    }
    
    print("\n📥 Downloading food images...\n")
    
    for filename, url in images.items():
        filepath = os.path.join('images', filename)
        
        if os.path.exists(filepath):
            print(f"⏭️  Skipped {filename} (already exists)")
            continue
        
        try:
            print(f"⬇️  Downloading {filename}...")
            urllib.request.urlretrieve(url, filepath)
            print(f"✅ Saved {filename}")
        except Exception as e:
            print(f"❌ Error downloading {filename}: {e}")
    
    print("\n✨ Download complete!")
    print(f"📁 Images saved in: {os.path.abspath('images')}")

if __name__ == "__main__":
    print("🍔 ByteBite Food Images Downloader")
    print("=" * 40)
    download_images()