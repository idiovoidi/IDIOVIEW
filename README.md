# ID:I/O VIEW
A PyQt6-based gallery viewer specifically designed for managing and viewing AI-generated images. This application provides a user-friendly interface for organizing, viewing, and managing your AI-generated artwork.

## 🌟 Features
### Image Management
- **Grid View**: Display images in a responsive, scrollable grid layout
- **Fullscreen Mode**: View images in Fullscreen with navigation controls
- **Image Sorting & Filtering**: Sort images by:
- Custom Metadata
- JSON Parsing for sorting AI content 
- Matplotlib & Seaborn to draw both fun and useful graphs

### Database Integration (retrieval only)
- SQLAlchemy-based database integration
- Retrieves image metadata and relationships
- Support for image categorization and tagging from databases

## 🔧 Installation
(Placeholder)

## 🛠️ Configuration

The application looks for images in the default InvokeAI output directory. You can modify this in the settings:

## 🐛 Issues

- Large image collections may require significant memory
- Some image formats may not be supported
- Initial loading time can be slow for large galleries
