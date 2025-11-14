/**
 * Enhanced admin interface for managing donation preset amounts
 * Provides real-time preview and validation
 */

(function($) {
    'use strict';
    
    $(document).ready(function() {
        console.log('Donation amounts admin JS loaded');
        
        // Get all amount input fields
        const amountFields = [];
        for (let i = 1; i <= 8; i++) {
            const field = $(`#id_amount_${i}`);
            if (field.length) {
                amountFields.push(field);
            }
        }
        
        console.log('Found amount fields:', amountFields.length);
        
        if (amountFields.length === 0) {
            console.log('No amount fields found, exiting');
            return;
        }
        
        // Create live preview container
        function createPreviewContainer() {
            const previewHtml = `
                <div id="donation-amounts-preview" style="margin: 15px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; background: #f9f9f9;">
                    <h4 style="margin: 0 0 10px 0; color: #333;">Live Preview</h4>
                    <p style="margin: 0 0 10px 0; font-size: 12px; color: #666;">This is how the donation amounts will appear to users:</p>
                    <div id="preview-amounts" style="margin: 10px 0;">
                        <em>Enter amounts above to see preview</em>
                    </div>
                    <div id="preview-stats" style="margin-top: 10px; font-size: 12px; color: #666;">
                        <span id="active-count">0</span> active amounts
                    </div>
                </div>
            `;
            
            // Insert after the last amount field
            const lastField = amountFields[amountFields.length - 1];
            const fieldRow = lastField.closest('.form-row, .field-amount_8');
            if (fieldRow.length) {
                fieldRow.after(previewHtml);
            } else {
                // Fallback: insert after the last amount field directly
                lastField.parent().after(previewHtml);
            }
        }
        
        // Update the live preview
        function updatePreview() {
            const amounts = [];
            
            // Collect non-empty amounts
            amountFields.forEach(field => {
                const value = parseFloat(field.val());
                if (!isNaN(value) && value > 0) {
                    amounts.push(value);
                }
            });
            
            const previewContainer = $('#preview-amounts');
            const statsContainer = $('#preview-stats');
            
            if (amounts.length === 0) {
                previewContainer.html('<em style="color: #999;">No amounts configured</em>');
                statsContainer.html('<span style="color: #d63384;">0 active amounts - Users will only see custom amount input</span>');
                return;
            }
            
            // Generate preview HTML
            let previewHtml = '';
            amounts.forEach((amount, index) => {
                previewHtml += `<span style="display: inline-block; margin: 3px; padding: 8px 12px; border: 1px solid #007cba; border-radius: 4px; background: #e7f3ff; color: #004085; font-weight: 500;">RM ${amount}</span>`;
                if ((index + 1) % 4 === 0) {
                    previewHtml += '<br>';
                }
            });
            
            previewContainer.html(previewHtml);
            
            // Update stats
            const totalAmounts = amounts.length;
            const minAmount = Math.min(...amounts);
            const maxAmount = Math.max(...amounts);
            
            statsContainer.html(`
                <span style="color: #198754;">${totalAmounts} active amounts</span> | 
                Range: RM ${minAmount} - RM ${maxAmount}
            `);
        }
        
        // Add input validation and formatting
        function setupFieldValidation() {
            amountFields.forEach((field, index) => {
                // Add placeholder
                field.attr('placeholder', `e.g., ${[10, 20, 30, 50, 100, 150, 200, 250][index] || '25.00'}`);
                
                // Add input event listener
                field.on('input', function() {
                    const value = $(this).val();
                    
                    // Remove any non-numeric characters except decimal point
                    const cleanValue = value.replace(/[^0-9.]/g, '');
                    
                    // Ensure only one decimal point
                    const parts = cleanValue.split('.');
                    if (parts.length > 2) {
                        $(this).val(parts[0] + '.' + parts.slice(1).join(''));
                    } else {
                        $(this).val(cleanValue);
                    }
                    
                    // Update preview
                    updatePreview();
                    
                    // Validate amount
                    const numValue = parseFloat(cleanValue);
                    if (!isNaN(numValue)) {
                        if (numValue < 0.01) {
                            $(this).css('border-color', '#dc3545');
                            $(this).attr('title', 'Amount must be at least RM 0.01');
                        } else if (numValue > 10000) {
                            $(this).css('border-color', '#ffc107');
                            $(this).attr('title', 'Very high amount - please verify');
                        } else {
                            $(this).css('border-color', '#198754');
                            $(this).attr('title', 'Valid amount');
                        }
                    } else if (cleanValue === '') {
                        $(this).css('border-color', '');
                        $(this).attr('title', 'Leave empty to disable this amount slot');
                    }
                });
                
                // Add blur event for formatting
                field.on('blur', function() {
                    const value = parseFloat($(this).val());
                    if (!isNaN(value) && value > 0) {
                        $(this).val(value.toFixed(2));
                        updatePreview();
                    }
                });
            });
        }
        
        // Add quick-set buttons
        function addQuickSetButtons() {
            const quickSetHtml = `
                <div id="quick-set-buttons" style="margin: 15px 0; padding: 10px; border: 1px solid #ddd; border-radius: 5px; background: #f0f8ff;">
                    <h4 style="margin: 0 0 10px 0; color: #333;">Quick Set Options</h4>
                    <button type="button" class="quick-set-btn" data-amounts="10,20,30,50,100" style="margin: 2px; padding: 5px 10px; border: 1px solid #007cba; background: #fff; border-radius: 3px; cursor: pointer;">Basic (5 amounts)</button>
                    <button type="button" class="quick-set-btn" data-amounts="10,20,30,50,100,150,200,250" style="margin: 2px; padding: 5px 10px; border: 1px solid #007cba; background: #fff; border-radius: 3px; cursor: pointer;">Full (8 amounts)</button>
                    <button type="button" class="quick-set-btn" data-amounts="5,10,25,50,100" style="margin: 2px; padding: 5px 10px; border: 1px solid #007cba; background: #fff; border-radius: 3px; cursor: pointer;">Small Amounts</button>
                    <button type="button" class="quick-set-btn" data-amounts="25,50,100,200,500" style="margin: 2px; padding: 5px 10px; border: 1px solid #007cba; background: #fff; border-radius: 3px; cursor: pointer;">Large Amounts</button>
                    <button type="button" id="clear-all-btn" style="margin: 2px; padding: 5px 10px; border: 1px solid #dc3545; background: #fff; color: #dc3545; border-radius: 3px; cursor: pointer;">Clear All</button>
                </div>
            `;
            
            // Insert before the first amount field
            const firstField = amountFields[0];
            const fieldRow = firstField.closest('.form-row, .field-amount_1');
            if (fieldRow.length) {
                fieldRow.before(quickSetHtml);
            } else {
                firstField.parent().before(quickSetHtml);
            }
            
            // Add event listeners for quick-set buttons
            $('.quick-set-btn').on('click', function() {
                const amounts = $(this).data('amounts').toString().split(',');
                
                // Clear all fields first
                amountFields.forEach(field => field.val(''));
                
                // Set the specified amounts
                amounts.forEach((amount, index) => {
                    if (index < amountFields.length) {
                        amountFields[index].val(parseFloat(amount).toFixed(2));
                        amountFields[index].css('border-color', '#198754');
                    }
                });
                
                updatePreview();
                
                // Visual feedback
                $(this).css('background', '#d4edda').delay(200).queue(function() {
                    $(this).css('background', '#fff').dequeue();
                });
            });
            
            // Clear all button
            $('#clear-all-btn').on('click', function() {
                if (confirm('Are you sure you want to clear all preset amounts?')) {
                    amountFields.forEach(field => {
                        field.val('');
                        field.css('border-color', '');
                    });
                    updatePreview();
                    
                    // Visual feedback
                    $(this).css('background', '#f8d7da').delay(200).queue(function() {
                        $(this).css('background', '#fff').dequeue();
                    });
                }
            });
        }
        
        // Initialize everything
        function init() {
            console.log('Initializing donation amounts admin interface');
            
            // Add enhancements
            addQuickSetButtons();
            createPreviewContainer();
            setupFieldValidation();
            
            // Initial preview update
            updatePreview();
            
            console.log('Donation amounts admin interface initialized');
        }
        
        // Run initialization
        init();
        
        // Add save confirmation
        $('form').on('submit', function() {
            const amounts = [];
            amountFields.forEach(field => {
                const value = parseFloat(field.val());
                if (!isNaN(value) && value > 0) {
                    amounts.push(value);
                }
            });
            
            if (amounts.length === 0) {
                return confirm('You have not set any preset amounts. Users will only be able to enter custom amounts. Continue?');
            }
            
            return true;
        });
    });
})(django.jQuery);
