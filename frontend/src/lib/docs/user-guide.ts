/**
 * User Guide documentation content.
 * Each section contains markdown content for the documentation.
 */

export interface DocSection {
	id: string;
	titleKey: string;
	content: string;
}

export const userGuideSections: DocSection[] = [
	{
		id: 'introduction',
		titleKey: 'docs.userGuide.introduction.title',
		content: `
## Welcome to StorageHub

StorageHub is a powerful home inventory management application that helps you organize, track, and find your belongings with ease. Whether you're managing a single closet or an entire household, StorageHub provides the tools you need to stay organized.

### Key Features

- **Hierarchical Organization**: Organize items using Locations, Containers, and Items
- **AI-Powered Classification**: Automatically categorize items using photos
- **QR Code Integration**: Generate and scan QR codes for quick access
- **Smart Search**: Find anything instantly with intelligent search
- **Sharing**: Share containers or locations with others via secure links
- **Reminders**: Set reminders for seasonal items or maintenance tasks
- **Multi-Language Support**: Available in English and Norwegian

### Getting Started

1. **Create a Location**: Start by adding your first location (e.g., "Home", "Office", "Storage Unit")
2. **Add Containers**: Create containers within locations (boxes, shelves, drawers)
3. **Add Items**: Populate containers with your belongings
4. **Generate QR Codes**: Print labels for physical containers
5. **Search and Find**: Use the search feature to locate items quickly
`
	},
	{
		id: 'hierarchy',
		titleKey: 'docs.userGuide.hierarchy.title',
		content: `
## Understanding the Hierarchy

StorageHub uses a three-level hierarchy to organize your belongings:

### Locations

Locations are the top-level organizational unit. They represent physical places where you store things.

**Examples:**
- Home
- Office
- Garage
- Storage Unit
- Vacation Home

### Containers

Containers exist within locations and can be nested inside other containers. They represent physical storage units.

**Container Types:**
- Box
- Drawer
- Shelf
- Cabinet
- Closet
- Bin
- Basket
- Other

**Nesting Example:**
\`\`\`
Home (Location)
└── Bedroom Closet (Container)
    ├── Top Shelf (Container)
    │   └── Winter Hats (Items)
    └── Bottom Drawer (Container)
        └── Socks (Items)
\`\`\`

### Items

Items are the individual belongings you want to track. Each item belongs to exactly one container.

**Item Properties:**
- Name and description
- Quantity
- Condition (Good, Fair, Damaged, Needs Repair)
- Purchase date and price
- Tags for categorization
- Photos
- Notes
`
	},
	{
		id: 'locations',
		titleKey: 'docs.userGuide.locations.title',
		content: `
## Managing Locations

Locations are the foundation of your organization system.

### Creating a Location

1. Navigate to the **Locations** page from the main navigation
2. Click **Add Location**
3. Enter a name (required) and optional address/description
4. Click **Create**

### Editing a Location

1. Navigate to the location you want to edit
2. Click the **Edit** button (pencil icon)
3. Modify the name or address
4. Click **Save**

### Deleting a Location

> **Warning:** Deleting a location will also delete all containers and items within it. This action cannot be undone.

1. Navigate to the location
2. Click the **Delete** button
3. Confirm the deletion in the dialog

### Location Overview

Each location page shows:
- Total number of containers
- Total number of items
- List of top-level containers
- Recent activity
`
	},
	{
		id: 'containers',
		titleKey: 'docs.userGuide.containers.title',
		content: `
## Working with Containers

Containers are versatile storage units that can hold items or other containers.

### Creating a Container

1. Navigate to a location or parent container
2. Click **Add Container**
3. Enter a name and select a type
4. Optionally add a description
5. Click **Create**

### Container Types

Choose the type that best describes your physical container:

| Type | Best For |
|------|----------|
| Box | Cardboard boxes, storage boxes |
| Drawer | Desk drawers, dresser drawers |
| Shelf | Bookshelf shelves, closet shelves |
| Cabinet | Kitchen cabinets, bathroom cabinets |
| Closet | Entire closets as containers |
| Bin | Plastic bins, storage totes |
| Basket | Baskets, hampers |
| Other | Anything that doesn't fit above |

### Nesting Containers

Containers can be nested to any depth. This is useful for complex organization:

1. Navigate to the parent container
2. Click **Add Container**
3. The new container is automatically placed inside the parent

### Moving Containers

To relocate a container:

1. Navigate to the container
2. Click **Move**
3. Select the new parent (location or container)
4. Click **Confirm**

### QR Codes

Each container automatically gets a unique QR code:

1. Navigate to the container
2. Click the **QR Code** button
3. Print or download the QR code
4. Attach it to the physical container
`
	},
	{
		id: 'items',
		titleKey: 'docs.userGuide.items.title',
		content: `
## Managing Items

Items are the individual belongings you track in StorageHub.

### Adding an Item

1. Navigate to a container
2. Click **Add Item**
3. Fill in the details:
   - **Name** (required): What is this item?
   - **Description**: Additional details
   - **Quantity**: How many do you have?
   - **Condition**: Current state of the item
   - **Purchase Date/Price**: Optional tracking info
   - **Tags**: Categorization labels
   - **Photos**: Visual reference

### Adding Photos

Photos help you identify and remember items:

1. While creating/editing an item, click **Add Photo**
2. Take a photo or upload from your device
3. AI can automatically classify the item based on the photo

### Using Tags

Tags help you categorize and find items:

1. Create tags from the **Tags** page
2. Assign colors to tags for visual distinction
3. Add tags to items when creating or editing
4. Search by tag to find related items

### Item Conditions

Track the state of your belongings:

- **Good**: Item is in working/normal condition
- **Fair**: Minor wear or issues
- **Damaged**: Significant damage but still usable
- **Needs Repair**: Requires attention before use

### Moving Items

To move an item to a different container:

1. Navigate to the item
2. Click **Move**
3. Select the destination container
4. Click **Confirm**

### Seasonal Items

Mark items as seasonal for easy filtering:
- Spring
- Summer
- Fall
- Winter
- Holiday
`
	},
	{
		id: 'ai-features',
		titleKey: 'docs.userGuide.aiFeatures.title',
		content: `
## AI Features

StorageHub uses artificial intelligence to help you organize faster and smarter.

### Photo Classification

When you add a photo to an item, AI can automatically:

1. **Identify the item**: Suggest what the item is
2. **Categorize**: Recommend appropriate tags
3. **Describe**: Generate a description

**How to use:**
1. Click **Add Photo** when creating an item
2. Take or upload a photo
3. Click **Classify with AI**
4. Review and accept the suggestions

### Smart Segmentation

For photos with multiple items:

1. Upload a photo containing multiple objects
2. Click **Segment Items**
3. AI identifies individual items in the photo
4. Create separate items from each detected object

### AI-Generated Summaries

Get insights about your containers:

1. Navigate to a container with items
2. Click **Generate Summary**
3. AI creates a brief overview of the contents

### Configuration

Administrators can configure AI settings:

- Enable/disable AI features
- Choose AI model (GPT-4, GPT-4 Mini, etc.)
- Set API keys

See the Admin Features section for details.
`
	},
	{
		id: 'searching',
		titleKey: 'docs.userGuide.searching.title',
		content: `
## Searching

StorageHub provides powerful search capabilities to help you find anything quickly.

### Quick Search

The search bar in the header provides instant results:

1. Click the search bar or press **/** on desktop
2. Type your search query
3. Results appear as you type
4. Click a result to navigate directly to it

### Search Page

For advanced searching, visit the dedicated Search page:

1. Click **Search** in the navigation
2. Enter your search terms
3. Use filters to narrow results
4. Sort results by relevance, date, or name

### What You Can Search

- **Items**: By name, description, or notes
- **Containers**: By name or description
- **Locations**: By name or address
- **Tags**: Items with specific tags

### Search Tips

- Use specific terms for better results
- Search for tags using the tag name
- Partial words work (e.g., "win" finds "winter")
- Search is case-insensitive

### Filters

Narrow your results using filters:

- **Type**: Items, Containers, or Locations
- **Location**: Limit to specific location
- **Tags**: Filter by tag
- **Condition**: Filter items by condition
- **Seasonal**: Filter by season

### Sort Options

- **Relevance**: Best matches first
- **Newest**: Recently created first
- **Oldest**: Oldest items first
- **Name (A-Z)**: Alphabetical order
- **Name (Z-A)**: Reverse alphabetical
`
	},
	{
		id: 'qr-codes',
		titleKey: 'docs.userGuide.qrCodes.title',
		content: `
## QR Codes

QR codes provide quick physical-to-digital access to your containers.

### How It Works

1. Each container has a unique QR code
2. Print and attach the QR code to the physical container
3. Scan the code with your phone to instantly view contents

### Viewing QR Codes

1. Navigate to any container
2. Click the **QR Code** button
3. The QR code displays in a modal

### Printing QR Codes

**Single Label:**
1. View the QR code for a container
2. Click **Print Label**
3. Select your printer and template
4. Print

**Batch Printing:**
1. Go to **God View**
2. Select multiple containers using checkboxes
3. Click **Print Selected**
4. Choose your printer and template
5. Print all labels at once

### Scanning QR Codes

**Using the Mobile App:**
1. Tap **Scan** in the bottom navigation
2. Point your camera at the QR code
3. The container opens automatically

**Using Any QR Scanner:**
- StorageHub QR codes contain URLs
- Any QR scanner will open the container in your browser

### Label Templates

Configure label appearance in printer settings:
- Container name
- QR code size
- Additional information
- Label dimensions

See the Printing Labels section for detailed setup.
`
	},
	{
		id: 'sharing',
		titleKey: 'docs.userGuide.sharing.title',
		content: `
## Sharing

Share containers or locations with others using secure links.

### Creating a Share Link

1. Navigate to a container or location
2. Click the **Share** button
3. Configure sharing options:
   - **Expiration**: When the link expires (or never)
   - **Allow item view**: Whether items are visible
4. Click **Create Link**
5. Copy and share the link

### Share Link Features

- **Read-only access**: Recipients can view but not edit
- **No login required**: Anyone with the link can view
- **Expiration control**: Set automatic expiration
- **View tracking**: See how many times links are accessed

### Managing Share Links

View and manage active share links:

1. Navigate to the container/location
2. Click **Share**
3. View active links under "Active Share Links"
4. Delete links you no longer need

### Security Considerations

- Share links grant read access to anyone who has them
- Use expiration dates for temporary sharing
- Delete links when no longer needed
- Shared containers show nested containers and items
- The original URL structure is not exposed
`
	},
	{
		id: 'reminders',
		titleKey: 'docs.userGuide.reminders.title',
		content: `
## Reminders

Set reminders to help you manage seasonal items and maintenance tasks.

### Creating a Reminder

1. Navigate to the **Reminders** page
2. Click **Add Reminder**
3. Fill in the details:
   - **Title**: What to remember
   - **Due Date**: When to be reminded
   - **Recurring**: Set up repeat schedule
   - **Link to Item/Container**: Optional association
4. Click **Create**

### Reminder Types

**One-time Reminders:**
- Single occurrence
- Good for specific tasks

**Recurring Reminders:**
- Repeat on a schedule
- Great for seasonal rotations
- Options: Daily, Weekly, Monthly, Yearly

### Use Cases

- **Seasonal Clothing**: "Switch to winter clothes" (yearly)
- **Maintenance**: "Check smoke detector batteries" (monthly)
- **Rotation**: "Rotate emergency food supplies" (quarterly)
- **Events**: "Pack holiday decorations" (yearly)

### Managing Reminders

**View Reminders:**
- **Pending**: Upcoming reminders
- **Overdue**: Past due reminders
- **Completed**: Finished reminders

**Mark Complete:**
1. Click the checkbox next to a reminder
2. For recurring reminders, the next occurrence is created

**Edit/Delete:**
1. Click on a reminder to view details
2. Use Edit or Delete buttons
`
	},
	{
		id: 'godview',
		titleKey: 'docs.userGuide.godview.title',
		content: `
## God View

God View provides a comprehensive tree view of your entire inventory.

### Accessing God View

Click **God View** in the main navigation.

### Features

**Tree Navigation:**
- Expandable/collapsible tree structure
- Shows all locations, containers, and items
- Click items to expand/collapse
- Visual indicators for container types

**Inline Editing:**
- Click any name to edit it directly
- Press Enter to save, Escape to cancel
- No page navigation required

**Quick Actions:**
- Add containers or items directly from the tree
- Delete items with confirmation
- Move items via drag-and-drop (coming soon)

### Batch Operations

**Selecting Items:**
1. Click checkboxes to select items
2. Use "Select All" for mass selection
3. Selected count shows in toolbar

**Batch Printing:**
1. Select multiple containers
2. Click **Print Selected**
3. All selected containers print at once

**Batch Delete:**
1. Select items to delete
2. Click **Delete Selected**
3. Confirm the operation

### Filtering

Use the toolbar filters to narrow the view:
- Search within tree
- Filter by location
- Filter by container type

### Keyboard Shortcuts

- **Arrow Keys**: Navigate tree
- **Enter**: Expand/collapse node
- **Space**: Toggle selection
- **Escape**: Clear selection
`
	},
	{
		id: 'printing',
		titleKey: 'docs.userGuide.printing.title',
		content: `
## Printing Labels

StorageHub supports printing QR code labels to various label printers.

### Supported Printers

**Zebra ZPL Printers:**
- Network-connected Zebra printers
- Uses ZPL (Zebra Programming Language)
- Supports various label sizes

**Brother QL Printers:**
- Brother QL series label printers
- Network or USB connection
- DK label support

**Generic PDF:**
- Outputs PDF files
- Print to any standard printer
- Good for testing

### Setting Up a Printer

1. Navigate to **Printers** page
2. Click **Add Printer**
3. Configure:
   - **Name**: Friendly name for the printer
   - **Type**: Zebra ZPL, Brother QL, or Generic PDF
   - **Connection**: Network address or file path
4. Click **Save**

### Network Printers

For network printers:
1. Ensure printer is on the same network
2. Enter the printer's IP address and port
3. Example: \`192.168.1.100:9100\`

### Test Printing

Always test your printer setup:
1. Navigate to the printer in settings
2. Click **Test Print**
3. Verify the test label prints correctly

### Label Templates

Configure what appears on labels:
- QR code (always included)
- Container name
- Location path
- Custom text

### Troubleshooting

**No output:**
- Verify network connectivity
- Check printer IP address
- Ensure printer is online

**Garbled output:**
- Verify correct printer type selected
- Check label size settings
- Update printer firmware
`
	},
	{
		id: 'settings',
		titleKey: 'docs.userGuide.settings.title',
		content: `
## Settings

Customize StorageHub to your preferences.

### Accessing Settings

Click your profile picture, then **Settings**.

### Profile

Update your personal information:
- **Name**: Your display name
- **Email**: Contact email (optional)
- **Password**: Set or change your password

### Appearance

**Theme:**
- **Light**: Light background, dark text
- **Dark**: Dark background, light text
- **System**: Follow your device settings

The theme applies immediately throughout the app.

### Language

Choose your preferred language:
- **English**: Full support
- **Norwegian (Norsk)**: Full support

The language setting syncs across all your devices.

### Data Export

Export your data for backup or analysis:

**JSON Export:**
- Complete data export
- Machine-readable format
- Includes all locations, containers, items

**CSV Export:**
- Spreadsheet-compatible format
- Good for reporting and analysis
- Separate files for each data type

### Statistics

View your storage statistics:
- Total locations
- Total containers
- Total items
- Storage distribution charts
`
	},
	{
		id: 'admin',
		titleKey: 'docs.userGuide.admin.title',
		content: `
## Admin Features

Administrators have access to additional management features.

### Accessing Admin Panel

1. Click your profile picture
2. Select **Admin Panel** (only visible to admins)

### User Management

**Creating Users:**
1. Click **Add User**
2. Enter name and optional password
3. Select role (Admin or User)
4. Click **Create**

**Editing Users:**
1. Click on a user
2. Modify details
3. Click **Save**

**Deleting Users:**
1. Click the delete icon
2. Confirm deletion
> Warning: This deletes all user data

### Activity Logs

View system-wide activity:
- Who did what and when
- Filter by user or action type
- Useful for auditing

### AI Configuration

Configure AI features:

**Enable/Disable AI:**
- Toggle AI features on or off
- Affects all users

**API Configuration:**
- Set OpenAI API key
- Choose model (GPT-4, GPT-4 Mini, etc.)
- Configure rate limits

**Model Selection:**
- GPT-4: Most capable, higher cost
- GPT-4 Mini: Faster, lower cost
- Custom: Use any OpenAI-compatible endpoint

### System Statistics

View overall system metrics:
- Total users
- Total storage items
- Database size
- API usage
`
	},
	{
		id: 'backup',
		titleKey: 'docs.userGuide.backup.title',
		content: `
## Backup & Restore

Protect your data with backup features.

### Manual Backup

**Export Data:**
1. Go to **Settings** > **Data**
2. Click **Export as JSON**
3. Save the downloaded file

**Restore Data:**
- Contact your administrator for restore procedures
- JSON backups can be imported by admins

### Google Drive Integration

Automatically backup to Google Drive:

**Setup (Admin):**
1. Go to **Admin Panel**
2. Navigate to **Google Drive Setup**
3. Follow OAuth authentication flow
4. Configure backup schedule

**Backup Options:**
- **Manual**: Trigger backup on demand
- **Daily**: Automatic daily backup
- **Weekly**: Automatic weekly backup

**What's Backed Up:**
- All locations
- All containers
- All items
- Item photos
- User settings

### Backup Best Practices

1. **Regular Backups**: Set up automatic backups
2. **Multiple Copies**: Keep backups in multiple locations
3. **Test Restores**: Periodically verify backups work
4. **Secure Storage**: Protect backup files

### Data Portability

Your data is yours:
- Export anytime in standard formats
- JSON export is human-readable
- CSV export works with spreadsheets
- No vendor lock-in
`
	}
];
