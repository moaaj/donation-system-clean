# Waqaf Asset Archive Functionality

This document describes the new archive functionality added to the Waqaf system, allowing administrators to archive and manage waqaf assets.

## Overview

The archive functionality allows administrators to:
- Archive waqaf assets to hide them from public view
- Unarchive assets to make them visible again
- Delete archived assets permanently
- View archived assets separately in the admin interface
- Track who archived assets and when

## New Model Fields

The `WaqafAsset` model now includes these additional fields:

- `is_archived`: Boolean field indicating if the asset is archived
- `archived_at`: DateTime field recording when the asset was archived
- `archived_by`: ForeignKey to User model, tracking who archived the asset

## Admin Interface Features

### 1. Archive Actions
- **Archive Assets**: Select assets and archive them in bulk
- **Unarchive Assets**: Select archived assets and unarchive them
- **Delete Archived Assets**: Permanently delete archived assets (with confirmation)
- **Archive Completed Assets**: Automatically archive fully funded assets
- **Bulk Unarchive All**: Unarchive all selected assets at once

### 2. Enhanced List Display
- Status column with color coding (Available, In Progress, Completed, Archived)
- Contribution count and total contributed amount
- Funding progress percentage
- Archive status and timestamp information

### 3. Custom Views
- **Archived Assets View**: Dedicated page showing all archived assets
- **Delete Confirmation**: Safe deletion with confirmation page

### 4. Quick Actions
- Archive/Unarchive buttons on individual asset change forms
- Color-coded status indicators
- Progress tracking for funding

## Public Interface Changes

- Archived assets are automatically hidden from public views
- Forms only show non-archived assets
- Asset detail pages return 404 for archived assets
- All public queries filter out archived assets

## Usage Instructions

### Archiving Assets

1. **Individual Asset**: 
   - Go to the asset's change form in admin
   - Click the "Archive Asset" button
   - Confirm the action

2. **Bulk Archive**:
   - Select multiple assets in the admin list
   - Choose "Archive selected assets" from the actions dropdown
   - Confirm the action

3. **Archive Completed Assets**:
   - Select assets (or all assets)
   - Choose "Archive completed assets (fully funded)" action
   - This will only archive assets with no available slots

### Unarchiving Assets

1. **Individual Asset**:
   - Go to the archived asset's change form
   - Click the "Unarchive Asset" button
   - Confirm the action

2. **Bulk Unarchive**:
   - Select archived assets
   - Choose "Unarchive selected assets" action

### Deleting Archived Assets

1. **Safe Deletion**:
   - Select archived assets
   - Choose "Delete selected archived assets" action
   - Review the confirmation page
   - Confirm deletion

### Viewing Archived Assets

1. **Admin List View**:
   - Use the "is_archived" filter to show only archived assets
   - Archive-related fields are moved to the front for better visibility

2. **Dedicated Archive View**:
   - Navigate to the "Archived Assets" custom view
   - See statistics and manage archived assets

## Migration

To apply the new functionality:

1. Run the migration:
   ```bash
   python manage.py migrate waqaf
   ```

2. The new fields will be added with default values:
   - `is_archived`: False (existing assets remain visible)
   - `archived_at`: None
   - `archived_by`: None

## Benefits

- **Better Asset Management**: Organize assets by status and funding progress
- **Public Experience**: Hide completed or outdated assets from public view
- **Audit Trail**: Track who archived assets and when
- **Safe Operations**: Confirmation pages prevent accidental deletions
- **Bulk Operations**: Efficiently manage multiple assets at once

## Security Considerations

- Only superusers and staff with appropriate permissions can archive/unarchive assets
- Deletion requires explicit confirmation
- Archive actions are logged with user and timestamp information
- Public interface automatically filters out archived assets

## Future Enhancements

Potential improvements for future versions:
- Archive reason/notes field
- Automatic archiving based on time or conditions
- Archive notification system
- Archive statistics and reporting
- Bulk import/export of archive status
