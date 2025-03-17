#!/usr/bin/env python3
"""
Script to update URL routes in Jinja2 templates to use the new blueprint-based structure.

This script scans all template files and updates url_for() calls to include
the appropriate blueprint prefix.
"""

import os
import re
import shutil
from pathlib import Path

# Map of old route names to new blueprint-prefixed routes
ROUTE_MAPPING = {
    # Auth routes
    "'login'": "'auth.login'",
    '"login"': '"auth.login"',
    "'logout'": "'auth.logout'",
    '"logout"': '"auth.logout"',
    "'register'": "'auth.register'",
    '"register"': '"auth.register"',
    "'request_reset'": "'auth.request_reset'",
    '"request_reset"': '"auth.request_reset"',
    "'reset_password'": "'auth.reset_password'",
    '"reset_password"': '"auth.reset_password"',
    "'test_email'": "'auth.test_email'",
    '"test_email"': '"auth.test_email"',
    
    # Control routes
    "'index'": "'controls.index'",
    '"index"': '"controls.index"',
    "'control_detail'": "'controls.control_detail'",
    '"control_detail"': '"controls.control_detail"',
    "'create_control'": "'controls.create_control'",
    '"create_control"': '"controls.create_control"',
    "'edit_control'": "'controls.edit_control'",
    '"edit_control"': '"controls.edit_control"',
    "'delete_control'": "'controls.delete_control'",
    '"delete_control"': '"controls.delete_control"',
    "'update_review_dates'": "'controls.update_review_dates'",
    '"update_review_dates"': '"controls.update_review_dates"',
    
    # Task routes
    "'add_task'": "'tasks.add_task'",
    '"add_task"': '"tasks.add_task"',
    "'edit_task'": "'tasks.edit_task'",
    '"edit_task"': '"tasks.edit_task"',
    "'complete_task'": "'tasks.complete_task'",
    '"complete_task"': '"tasks.complete_task"',
    "'confirm_task'": "'tasks.confirm_task'",
    '"confirm_task"': '"tasks.confirm_task"',
    "'delete_task'": "'tasks.delete_task'",
    '"delete_task"': '"tasks.delete_task"',
    "'calendar'": "'tasks.calendar'",
    '"calendar"': '"tasks.calendar"',
    
    # Report routes
    "'reports'": "'reports.reports'",
    '"reports"': '"reports.reports"',
    
    # Admin routes
    "'admin_users'": "'admin.admin_users'",
    '"admin_users"': '"admin.admin_users"',
    "'admin_create_user'": "'admin.admin_create_user'",
    '"admin_create_user"': '"admin.admin_create_user"',
    "'admin_edit_user'": "'admin.admin_edit_user'",
    '"admin_edit_user"': '"admin.admin_edit_user"',
    "'admin_delete_user'": "'admin.admin_delete_user'",
    '"admin_delete_user"': '"admin.admin_delete_user"',
    "'audit_logs'": "'admin.audit_logs'",
    '"audit_logs"': '"admin.audit_logs"',
}

def create_backup(templates_dir):
    """Create a backup of the templates directory."""
    backup_dir = templates_dir.parent / (templates_dir.name + "_backup")
    if backup_dir.exists():
        print(f"Backup directory already exists: {backup_dir}")
        return backup_dir
    
    shutil.copytree(templates_dir, backup_dir)
    print(f"Created backup of templates at: {backup_dir}")
    return backup_dir

def update_template_file(file_path):
    """Update url_for() calls in a template file."""
    print(f"Processing: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Track number of replacements
    replacement_count = 0
    original_content = content
    
    # Update url_for() calls more robustly
    for old_route, new_route in ROUTE_MAPPING.items():
        # Create a more precise replacement pattern
        pattern = rf'url_for\(\s*{re.escape(old_route)}\s*(?=,|\))'
        
        # Count and replace occurrences
        matches_count = len(re.findall(pattern, content))
        if matches_count > 0:
            content = re.sub(pattern, f'url_for({new_route}', content)
            replacement_count += matches_count
    
    # If changes were made, write back to the file
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  ✓ Updated {replacement_count} routes")
    else:
        print("  ✓ No changes needed")
    
    return replacement_count

def update_templates(templates_dir):
    """Update all template files in the given directory."""
    templates_path = Path(templates_dir)
    
    if not templates_path.exists() or not templates_path.is_dir():
        print(f"Error: Templates directory not found: {templates_dir}")
        return 0
    
    # Create backup first
    create_backup(templates_path)
    
    # Track total replacements
    total_replacements = 0
    
    # Process all HTML files
    for file_path in templates_path.glob('**/*.html'):
        if file_path.is_file():
            replacements = update_template_file(file_path)
            total_replacements += replacements
    
    return total_replacements

def main():
    """Main entry point for the script."""
    print("=" * 60)
    print("Template URL Route Updater")
    print("=" * 60)
    print("This script will update url_for() calls in your templates")
    print("to use the new blueprint-based route structure.")
    print()
    
    # Get templates directory
    templates_dir = input("Enter the path to your templates directory [app/templates]: ")
    if not templates_dir:
        templates_dir = "app/templates"
    
    # Confirm before proceeding
    print(f"\nAbout to update template routes in: {templates_dir}")
    print("A backup will be created before making any changes.")
    confirm = input("Continue? (y/n): ")
    
    if confirm.lower() != 'y':
        print("Operation cancelled.")
        return
    
    # Update templates
    total_replacements = update_templates(templates_dir)
    
    print("\nSummary:")
    print(f"Total route replacements: {total_replacements}")
    print("Backup created at: " + templates_dir + "_backup")
    print("\nPlease review the changes and test your application.")

if __name__ == "__main__":
    main()