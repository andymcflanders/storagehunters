# StorageHub User Guide

Welcome to StorageHub! This guide will help you organize and manage your belongings efficiently.

---

## Table of Contents

1. [Getting Started](#getting-started)
2. [Understanding the Hierarchy](#understanding-the-hierarchy)
3. [Managing Locations](#managing-locations)
4. [Working with Containers](#working-with-containers)
5. [Managing Items](#managing-items)
6. [Using AI Features](#using-ai-features)
7. [Searching Your Inventory](#searching-your-inventory)
8. [QR Codes](#qr-codes)
9. [Sharing with Others](#sharing-with-others)
10. [Setting Reminders](#setting-reminders)
11. [God View - Complete Inventory](#god-view---complete-inventory)
12. [Outgrown](#outgrown)
13. [Declutter (Tinder for Items)](#declutter-tinder-for-items)
14. [Printing Labels](#printing-labels)
15. [Settings & Preferences](#settings--preferences)
16. [Admin Features](#admin-features)
17. [Backup & Restore](#backup--restore)
18. [Tips & Best Practices](#tips--best-practices)

---

## Getting Started

### First-Run Setup (admins only)

When you visit a freshly-deployed StorageHub instance, the app detects the
empty database and redirects you to a setup wizard. The wizard walks you
through:

1. **Welcome** — short intro
2. **Administrator account** — name, email, password, and your interface
   language. This account is for setup and configuration only — keep it
   separate from your household identity. You'll add household users
   afterwards.
3. **AI features** (skippable) — paste an OpenAI API key and pick the
   languages you want the AI to generate item names and descriptions in
   (defaults to English + Norwegian). Both can be changed later under
   Admin → AI Settings.
4. **First location** (skippable) — name your first storage location.
5. **Done** — click "Open StorageHub" and you land on the dashboard,
   already signed in.

The wizard is one-shot — once an admin exists, `/setup` redirects back
to the app and the bootstrap endpoint refuses any further calls.

### Logging In

The login screen has two paths:

- **Household members**: tap your card on the user grid; if the account
  has a password, type it in the modal.
- **Administrators**: click the **Administer this instance** link below
  the grid and sign in with email + password. Admin accounts are
  intentionally hidden from the card grid so they don't get used as
  everyday accounts.

If you don't have an account, ask an admin to create one — or, if the
instance hasn't been onboarded yet, run the wizard above.

### Dashboard Overview

After logging in, you'll see the dashboard with:
- **Quick Stats**: Total locations, containers, items, and photos
- **Location Cards**: Quick access to your storage areas

The activity log lives in the Admin panel, not on the dashboard.

### Mobile vs Desktop

StorageHub is fully responsive:
- **Desktop**: Full-featured interface with side navigation
- **Mobile**: Optimized layout with camera access for quick scanning

---

## Understanding the Hierarchy

StorageHub organizes your belongings in a three-level hierarchy:

```
LOCATION (Where)
    └── CONTAINER (What holds things)
            └── ITEM (The thing itself)
```

**Example:**
```
Garage (Location)
    └── Blue Storage Bin (Container)
            └── Winter Jacket (Item)
            └── Snow Boots (Item)
    └── Tool Cabinet (Container)
            └── Drawer 1 (Nested Container)
                    └── Screwdrivers (Item)
```

### Nested Containers

Containers can hold other containers! This is useful for:
- Drawers within cabinets
- Small boxes inside large boxes
- Compartments within organizers

---

## Managing Locations

Locations represent physical storage areas like rooms, buildings, or storage units.

### Creating a Location

1. From the dashboard, click **+ New Location**
2. Enter the location name (e.g., "Garage", "Attic")
3. Optionally add:
   - Description
   - Physical address
4. Click **Create**

### Editing a Location

1. Navigate to the location
2. Click the **Edit** button (pencil icon)
3. Update the information
4. Click **Save**

### Deleting a Location

1. Navigate to the location
2. Click **Delete**
3. Confirm the deletion

**Warning:** Deleting a location permanently deletes ALL containers and
items inside it. There is no emptiness check — the deletion cascades
immediately, so double-check before confirming.

---

## Working with Containers

Containers are the boxes, bins, shelves, or any storage unit that holds your items.

### Creating a Container

1. Navigate to a location
2. Click **+ Add Container**
3. Enter the container name
4. **Optionally pick a type** — Box, Drawer, Shelf, Cabinet, Closet,
   Bin, Basket, or Other. The type shows up as a small badge on the
   container card and detail page.
5. **Optionally take a hero image** — tap "Take photo" to use the
   device camera. The image is shown as a thumbnail on the container
   card and full-size on the detail page. You can also add or replace
   the image later from the container detail page.
6. Optionally add notes
7. Click **Create**

A unique QR code is automatically generated!

### Editing a Container

From the container detail page:

- **Edit** button (top-right) — change the name, type, or notes.
- **Hero image** — when no image is set, the inline card has a
  "Take photo" button. With an image, **Replace image** swaps it,
  **Remove image** clears it. Camera access works on phones, laptops,
  and any browser that supports `getUserMedia`.

### Creating Nested Containers

1. Open a container
2. Click **+ Add Container** (within the container view)
3. The new container will be nested inside the parent

### Moving Containers

There is no Move button on the container page. To reorganize:

- Move individual items between containers with drag-and-drop in
  [God View](#god-view---complete-inventory).
- To empty one container into another, use the **Transfer** option when
  deleting it (see below).

### Deleting Containers

When deleting a container with contents, you have three options:

1. **Delete Everything** (Recursive)
   - Deletes the container AND all items inside
   - Also deletes any nested containers
   - Use with caution!

2. **Transfer Items First**
   - Moves all items to another container
   - Then deletes the empty container
   - Safer option for preserving items

3. **Cancel**
   - If the container is empty, it deletes immediately
   - If it has contents, a dialog appears with options

---

## Managing Items

Items are the individual belongings you're tracking.

### Adding Items

**Method 1: Manual Entry**
1. Navigate to a container
2. Click **+ Add Item**
3. Fill in the details:
   - Name (required)
   - Description
   - Size
   - Condition
   - Seasonal category
   - Estimated value
   - Owner
4. Click **Create**

**Method 2: Photo Upload with AI**
1. Navigate to a container
2. Click **+ Add with Photo**
3. Take a photo or upload an image
4. AI will automatically:
   - Generate a name
   - Create a description
   - Add relevant tags
5. Review and edit as needed
6. Click **Save**

### Item Properties

| Property | Description | Options |
|----------|-------------|---------|
| Name | Item name | Free text |
| Description | Detailed description | Free text |
| Size | Size information | Free text (e.g., "M", "42", "10x20cm") |
| Condition | Item condition | Good, Fair, Damaged, Needs Repair |
| Seasonal | When item is used | None, Spring, Summer, Fall, Winter, Holiday |
| Value | Estimated value | Number |
| Owner | Who owns this | Select from users |
| Tags | Categories/labels | Multiple selection |

### Managing Item Images

**Adding Images:**
1. Open an item
2. Click **Add Image** or drag & drop
3. Images are automatically processed by AI

**Setting Primary Image:**
1. Click on an image
2. Click **Set as Primary**
3. This image becomes the thumbnail

**Deleting Images:**
1. Hover over an image
2. Click the trash icon
3. Confirm deletion

### Moving Items

1. Open the item
2. Click **Move**
3. Select the destination container
4. Click **Move**

Or use drag-and-drop in God View!

### Adding Tags

**Manual Tags:**
1. Open an item
2. In the Tags section, type a tag name
3. Press Enter or click **Add**

**AI Tags:**
- Automatically generated when you upload images
- Appear with an "AI" badge
- Can be removed like manual tags

---

## Using AI Features

StorageHub uses AI to make inventory management easier.

### Automatic Classification

When you upload an image, AI automatically:
1. Identifies the item type
2. Generates a descriptive name
3. Creates a detailed description
4. Adds relevant tags
5. Provides translations in every language listed under
   **Admin → AI Settings → Languages** (defaults to English + Norwegian;
   add codes like `de` or `sv` to extend without a code change)

The user's profile language picks which translation is shown in the UI;
items fall back to the configured default language when the user's
locale is missing.

### Reprocessing Images

If AI results aren't satisfactory:
1. Open the item
2. Click **Reprocess with AI**
3. New tags and descriptions are generated
4. Review and save changes

### AI Owner Suggestion

When an item is classified, the AI also picks the most likely owner
from your household — matching item size + motif against each
non-admin user's age (computed from `birthdate`) and `gender`. A
size-98 dinosaur tee fits a toddler boy; size-42 wool socks fit any
adult.

The suggestion appears as a purple banner on the item page when
`owner_id` is still empty:

> **Suggested owner: Sverre** — *"size 98 dinosaur tee fits a toddler boy"*  
> [Assign to Sverre] [Dismiss]

- **Assign** patches the item's owner and clears the suggestion in
  one click.
- **Dismiss** clears the suggestion without setting an owner.
- Picking an owner manually via the edit form also clears the
  suggestion automatically.

The suggestion is *never* auto-applied — you always confirm. If a
suggestion looks wrong, dismiss it and the item won't resurface in
the same banner.

Admins can toggle the feature globally under **Admin → AI Settings**
(*AI Owner Suggestion*). When off, the vision prompt skips the
candidate-owners section entirely and items don't get a
`suggested_owner_id` populated.

---

## Searching Your Inventory

StorageHub's search understands natural language.

### Basic Search

Type in the search bar:
- Item names: "winter jacket"
- Descriptions: "red dress"
- Tags: "electronics"

### Smart Search Features

**Color Understanding:**
- "emerald sweater" finds green sweaters
- "navy pants" finds blue pants
- "crimson shirt" finds red shirts

**Synonym Recognition:**
- "cardigan" also finds sweaters
- "trousers" also finds pants

**Owner Search:**
- "Sarah's books" finds items owned by Sarah
- Include owner names in your search

**Natural Language:**
- "red dress size 104"
- "Christmas decorations in garage"
- "John's winter clothes"

### Search Filters

Refine results with filters:
- **Owner**: Filter by item owner
- **Location**: Search within a location
- **Container**: Search within a container
- **Condition**: Good, Fair, Damaged, etc.
- **Seasonal**: Filter by season
- **Tags**: Filter by specific tags

### Search Results

Results are ranked by relevance:
1. **Exact matches** (highlighted) - highest priority
2. **Similar matches** - partial word matches
3. **Semantic matches** - conceptually related

---

## QR Codes

Every container has a unique QR code for quick access.

### Scanning QR Codes

**In the App:**
1. Click the **Scan** icon in the navigation
2. Point your camera at a QR code
3. The container opens automatically

**With Any QR Scanner:**
- Codes contain URLs
- Scanning with any app opens StorageHub

### Viewing QR Codes

1. Open a container
2. Click the **QR Code** button
3. View or download the code

### Printing QR Labels

See [Printing Labels](#printing-labels) section.

---

## Sharing with Others

Share containers with people who don't have accounts.

### Creating a Share Link

1. Open a container
2. Click **Share**
3. Configure options:
   - **Show Items**: Whether to display item details
   - **Expiration**: Optional end date
4. Click **Create Link**
5. Copy and share the URL

### Share Link Options

| Option | Description |
|--------|-------------|
| Show Items | Toggle item visibility |
| Expiration | Auto-disable after date |
| Active/Inactive | Manually enable/disable |

### Managing Share Links

1. Go to the container
2. Click **Share**
3. See all existing links
4. Toggle active status or delete

### Accessing Shared Links

Recipients:
1. Open the shared URL
2. View container contents (no login required)
3. Cannot edit or modify anything

---

## Setting Reminders

Never forget to check on your items.

### Creating a Reminder

1. Go to **Reminders** in the menu
2. Click **+ New Reminder**
3. Fill in:
   - Title
   - Due date
   - Type (Check Item, Expiration, etc.)
   - Optional: Link to item or container
   - Optional: Make it recurring
4. Click **Create**

### Reminder Types

| Type | Use Case |
|------|----------|
| Check Item | Periodic inspection |
| Expiration | Items that expire (food, medications) |
| Maintenance | Equipment servicing |
| Restock | Inventory replenishment |
| Custom | Anything else |

### Recurring Reminders

1. Enable "Recurring" when creating
2. Set the interval (days between reminders)
3. When completed, a new reminder is auto-created

### Managing Reminders

**View Upcoming:**
- Dashboard shows next reminders
- Reminders page shows all

**Complete a Reminder:**
1. Click **Complete**
2. Reminder is marked done
3. If recurring, next one is created

**Edit/Delete:**
1. Open the reminder
2. Click Edit or Delete

---

## God View - Complete Inventory

God View shows your entire inventory in one place.

### Accessing God View

Click **God View** in the navigation menu.

### Interface Overview

The tree view shows:
- **Locations** (top level, colored header)
- **Containers** (indented, with item counts)
- **Items** (further indented, with thumbnails)

### Navigation

- **Expand/Collapse**: Click arrows to show/hide contents
- **Expand All**: Button to open everything
- **Collapse All**: Button to close everything

### Filtering

**Location Filter:**
1. Click **Locations** dropdown
2. Select specific locations
3. Only those locations appear

**Container Filter:**
1. Click **Containers** dropdown
2. Select specific containers
3. Only selected containers and their items appear

### Inline Editing

Edit anything directly in the table:
1. Click on any field (name, description, etc.)
2. Type your changes
3. Press Enter or click away to save

### Creating Containers

1. Hover over a location row
2. Click the **+** button
3. Enter container name
4. Container is created instantly

### Moving Items (Drag & Drop)

1. Grab an item by the drag handle (dots icon)
2. Drag to another container
3. Drop to move

### Deleting

Click the trash icon on any row to delete:
- Locations (**warning:** deletes all containers and items inside — the
  deletion cascades, there is no emptiness check)
- Containers (shows options if has contents)
- Items (immediate delete)

### Batch Printing Labels

Print labels for several containers at once:

1. Tick the checkbox on each container row you want a label for
2. Click **Print labels for checked containers** in the toolbar
3. Select your printer and confirm

Alternatively, apply a container filter and click **Print labels for
filtered containers** to print every container currently shown.

Labels include:
- Container name
- QR code
- AI-generated summary (if enabled)

### Expanded Item View

Click the arrow on an item row to expand:
- Full-size image (clickable to item page)
- All item fields
- AI-generated content
- Edit all properties inline

---

## Outgrown

The **Outgrown** view (top-nav, next to God View) surfaces items the
household has aged out of — Sverre's size-92 parka when he's now 5,
Sonja's outgrown shoes — so they don't sit in a far corner forever.

### How items get here

When an item is classified, the AI also estimates an age range for
its size (in months). Children's height-cm clothing sizes and EU shoe
sizes have well-defined mappings: size 92 covers ~18–24 months, size
116 covers ~60–72 months, EU 28 shoes ~48–60 months, etc. Adult
sizes leave the range blank — adult items don't show up here.

The page lists items where the *effective owner's* current age in
months is past the size's upper bound. The "effective owner" is the
real `owner_id` if set, otherwise the AI's suggested owner.

### Inherit-to suggestions

For each outgrown item, the page checks whether another household
member fits the size today, or will fit within ~12 months. If a match
exists, the row shows a green inherit suggestion:

> → Inherit to Sonja (fits in ~6 months)

- **Reassign** moves the item to the suggested user and removes it
  from the Outgrown view.
- **Dismiss** hides the item from the view (it stays in inventory at
  its current location). Dismissed items don't reappear unless their
  size or the owner's age data changes.

Items grouped by current owner; sorted most-outgrown first. Click the
item name to jump to its detail page.

### Backfilling existing items

Items added before the size-age feature shipped have a `size` string
but no age range, so they don't show up here yet. Admins can run
**Admin → AI Settings → Recompute Size Age Ranges** to backfill.
The action queues a Celery task that calls a cheap text-only model
once per item and is safe to re-run.

---

## Declutter (Tinder for Items)

The **Declutter** view (top-nav, also in the mobile bottom nav) shows
one item at a time and asks for a verdict: 🗑️ **Toss** · 🤔 **Maybe** ·
❤️ **Love**. The bottleneck of "what do I keep?" replaces the
bottleneck of "where do I even start?".

### The flow

1. Open `/declutter` (mobile: tap the heart icon in the bottom nav).
2. Review the current item: image, name, size, owner, container path,
   tags, description.
3. Decide:
   - **Love** — hidden from the deck for 12 months.
   - **Maybe** — comes back in 3 months.
   - **Toss** — moves to the discard pile (no cooldown).
4. The next card loads automatically. A counter at the top shows how
   many items you've reviewed in this session.

Decisions are *shared* per household (one row per item). If your
spouse hits Toss on something you'd keep, you'll see it on the
discard pile and can Undo from there.

### Filtering

A **Filters** toggle in the page header reveals two dropdowns:

- **Owner** — only items owned by this user.
- **Tag** — only items tagged with this tag (top-30 tags by
  eligible-item count).

Use them to focus a session — e.g. "Anders's t-shirts" or "Sonja's
toys". Combine them for narrower cohorts.

### Mobile swipe gestures

On phones the card responds to swipe gestures:

- **→ Right** = Love
- **← Left** = Toss
- **↑ Up** = Maybe

Visual stamps fade in as you drag past the threshold so you can
preview your decision before releasing. Below the threshold the card
snaps back. The three buttons remain visible for accessibility and
desktop use.

### What's excluded from the deck

- Items currently in cooldown (loved last year, undecided last month).
- Items already on the discard pile (Toss decisions).
- Items with an age range (handled by **Outgrown** instead — no
  double-surfacing).
- Items still being AI-processed (no point reviewing a placeholder
  card).

When the deck is exhausted, the page shows "You're all caught up."

### The Discard pile

Click **Discard pile →** to see everything you've marked Toss,
grouped by container path so a single physical sweep handles a
whole shelf.

Per-row actions:

- **Delete** — permanent removal from inventory (with confirm).
- **Donated** — soft-delete with a "(donated)" entry in the activity
  log. Captures intent rather than just "row vanished".
- **Undo** — clears the decision; the item returns to the deck.

---

## Printing Labels

Print QR code labels for your containers.

### Setting Up a Printer

1. Go to **Printers** in the menu
2. Click **+ Add Printer**
3. Configure:
   - Name
   - Printer Type (Zebra, Brother, PDF)
   - Connection (Network, USB, File)
   - Address/Port
   - Label size
4. Click **Test Connection**
5. Click **Save**

### Supported Printers

| Type | Best For |
|------|----------|
| Zebra ZPL | Thermal label printers |
| Brother QL | Consumer label makers |
| Generic PDF | Any printer (saves as PDF) |

### Printing a Label

1. Open a container
2. Click **Print Label**
3. Select printer
4. Preview the label
5. Click **Print**

### Label Contents

Labels include:
- Container name
- QR code
- Optional: Item count summary

---

## Settings & Preferences

### User Settings

Access via the gear icon or **Settings** menu.

**Profile:**
- Change your name
- Update email

**Language:**
- English
- Norwegian
- Selects the UI language and which stored AI translation is displayed.
  The languages the AI *generates* content in are configured separately
  under **Admin → AI Settings → Languages**.

**Theme (Dark Mode):**
StorageHub includes a full dark theme:
- Light mode - bright interface
- Dark mode - dark interface, easier on the eyes
- System preference - follows your device settings

Toggle dark mode from the settings page or use the theme button in the navigation.

### Changing Password

1. Go to Settings
2. Click **Change Password**
3. Enter current password
4. Enter new password twice
5. Click **Save**

---

## Admin Features

*Available to users with Admin role only.*

### Accessing Admin Panel

Click **Admin** in the navigation menu.

### User Management

**View Users:**
- See all users
- Search by name/email
- View role and status

**Create User:**
1. Click **+ New User**
2. Enter name, email
3. Set role (Admin/User)
4. Set initial password (optional)
5. Optionally tick **Profile (no login)** for household members who
   own items but won't sign in (e.g. small kids). Profile users are
   hidden from the login card grid.
6. Optionally set **Birthdate** and **Gender** — both feed the AI
   owner suggestion and the Outgrown view.
7. Click **Create**

**Edit User:**
1. Click on a user
2. Modify details (including Profile / Birthdate / Gender)
3. Click **Save**

> Admins cannot be marked as profile users — a profile-flagged admin
> couldn't log in via either path. The form enforces this both on
> create and edit.

**Delete User:**
1. Click delete icon
2. Confirm deletion

### Activity Logs

View all system activity:
- Who did what
- When it happened
- What changed (old vs new values)

Filter by:
- User
- Action type (Created, Updated, Deleted)
- Entity type (Item, Container, etc.)

### System Statistics

Dashboard shows:
- Total users (active, admins)
- Total locations, containers, items
- Recent activity count
- 30-day growth

### AI Settings

**OpenAI Classification Settings:**
Configure the AI models used for item classification:

1. **Vision Classification** (for analyzing uploaded images):
   - Enable/disable vision processing
   - Select model (gpt-4o, gpt-4o-mini, gpt-4-turbo)
   - Adjust max tokens (response length)
   - Set temperature (0.0-1.0, lower = more consistent)
   - View estimated cost per image

2. **Summary Generation** (for container labels):
   - Enable/disable AI summaries
   - Select model (gpt-4o-mini, gpt-4o)
   - Adjust max tokens
   - Set temperature
   - View estimated cost per summary

3. **AI Owner Suggestion**:
   - Toggle whether the vision classifier also picks the most likely
     owner from non-admin users (using birthdate + gender).
   - When off, the prompt skips the candidate-owners section entirely
     and items don't get a `suggested_owner_id`.

4. **Recompute Size Age Ranges**:
   - One-shot backfill that infers the kid-size → age-range mapping
     for every item with a `size` string but no age range yet. Drives
     the **Outgrown** view.
   - Cheap text-only AI call per item; idempotent (safe to re-run).

The admin panel shows real-time cost estimates based on current settings, helping you balance quality vs. cost.

---

## Backup & Restore

*Available to users with Admin role only.*

StorageHub includes a comprehensive backup system to protect your inventory data.

### Accessing Backup Settings

1. Go to **Admin** in the navigation menu
2. Click the **Backups** tab

### Creating a Manual Backup

1. Click **Create Backup Now**
2. Wait for the backup to complete
3. The backup appears in the list with timestamp and size

### Downloading Backups

1. Find the backup in the list
2. Click the **Download** button
3. A compressed archive is downloaded containing your complete database

### Restoring from Backup

**Note:** Restoring MERGES the backup into your current database — existing
rows are kept, and entries from the backup that already exist (matched by
name or QR code) are skipped rather than overwritten.

1. Find the backup you want to restore
2. Click **Restore**
3. Confirm the restoration
4. Wait for the process to complete
5. The restored data is merged into your inventory

### Automatic Backups

Configure scheduled backups to run automatically:

1. In Backup Settings, enable **Automatic Backups**
2. Set the frequency (daily, weekly, or custom interval)
3. Configure retention (how many backups to keep)
4. Backups run automatically at the scheduled time

### Google Drive Integration

Sync backups to Google Drive for off-site storage:

**Setting Up Google Drive:**
1. Create a Google Cloud service account and download its JSON key file
2. In the Backup section, add a Google Drive provider and paste the
   service-account JSON credentials (there is no OAuth sign-in flow)
3. Share a **Shared Drive** with the service account — service accounts
   need a Shared Drive to upload files; regular shared folders won't work

**Automatic Sync:**
- Once configured, backups are automatically uploaded to Google Drive
- Backups are stored in a "StorageHub Backups" folder
- Old backups are automatically cleaned up based on retention settings

**Manual Sync:**
- Click **Sync Now** to upload the latest backup
- Click **List Backups** to see backups stored in Google Drive

### Backup Contents

Each backup includes:
- All locations, containers, and items (with their tag assignments)
- Tags
- Image metadata
- User accounts (when the backup's include-users option is enabled)

NOT included: reminders, share links, activity logs, and system
configuration (printers, AI settings, etc.).

**Note:** The image files themselves are included only when the backup
config's **include images** option is enabled. Otherwise, consider backing
up the `uploads/` directory separately.

---

## Tips & Best Practices

### Organizing Your Inventory

1. **Use Descriptive Names**
   - "Winter Clothes - Kids" not "Box 1"
   - "Kitchen Gadgets - Small Appliances" not "Stuff"

2. **Take Good Photos**
   - Good lighting
   - Clear, uncluttered background
   - Show the whole item

3. **Use Tags Consistently**
   - Create a tag system
   - Merge duplicate tags periodically

4. **Set Owners**
   - Track who owns what
   - Useful for families or shared spaces

### Leveraging AI

1. **Let AI Do the Work**
   - Upload photos instead of typing
   - Review and refine AI suggestions

2. **Search Naturally**
   - "mom's winter coat" works!
   - Use colors and descriptions

### QR Code Workflow

1. **Print Labels Early**
   - Label containers when you create them
   - Stick QR codes on the outside

2. **Scan to Inventory**
   - Open container by scanning
   - Add items directly

### Maintenance

1. **Review Periodically**
   - Filter God View by `Needs Review = Yes` to find items the AI
     flagged or that you marked manually
   - Update conditions as items age

2. **Set Reminders**
   - Expiration dates for perishables
   - Seasonal rotation reminders

3. **Export Backups**
   - Periodically export JSON backup
   - Store securely

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Esc` | Close modal/cancel |
| `Enter` | Confirm/save |

---

## Troubleshooting

### Can't Log In
- Check email/password
- Contact admin for password reset
- Ensure account is active

### Images Not Processing
- Check file size (default limit is 10 MB, configurable via `MAX_UPLOAD_SIZE_MB`)
- Supported formats: JPG, PNG, GIF, WebP
- Wait for AI processing — items show an "Analyzing…" badge until done.
  AI requires `OPENAI_API_KEY` set either via the env var or
  Admin → AI Settings; without it, items get mock-classified placeholders.

### QR Code Not Scanning
- Ensure good lighting
- Hold camera steady
- Try different distance

### Search Not Finding Items
- Check spelling
- Try different terms
- Use fewer filters

### Need Help?

Contact your system administrator or check the documentation.

---

*StorageHub - Organize Everything, Find Anything*
