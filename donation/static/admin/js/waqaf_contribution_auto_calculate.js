(function($) {
    'use strict';
    
    // Function to calculate amount based on slots and asset price
    function calculateAmount() {
        var assetSelect = $('#id_asset');
        var slotsInput = $('#id_number_of_slots');
        var amountField = $('#id_amount');
        
        if (assetSelect.val() && slotsInput.val()) {
            // Get the selected asset's slot price from the option text or data attribute
            var selectedOption = assetSelect.find('option:selected');
            var optionText = selectedOption.text();
            
            // Try to extract slot price from option text (format: "Asset Name (X slots available)")
            var slotPriceMatch = optionText.match(/\(.*?(\d+(?:\.\d{2})?)\s*per slot/i);
            var slotPrice = 0;
            
            if (slotPriceMatch) {
                slotPrice = parseFloat(slotPriceMatch[1]);
            } else {
                // Fallback: try to get from data attribute
                slotPrice = parseFloat(selectedOption.data('slot-price')) || 0;
            }
            
            var numberOfSlots = parseInt(slotsInput.val()) || 0;
            var calculatedAmount = slotPrice * numberOfSlots;
            
            // Update the amount field
            amountField.val(calculatedAmount.toFixed(2));
            
            // Add visual feedback
            amountField.addClass('calculated-amount');
            setTimeout(function() {
                amountField.removeClass('calculated-amount');
            }, 2000);
            
            // Show calculation info
            showCalculationInfo(slotPrice, numberOfSlots, calculatedAmount);
        }
    }
    
    // Function to show calculation information
    function showCalculationInfo(slotPrice, numberOfSlots, calculatedAmount) {
        var infoDiv = $('#calculation-info');
        if (infoDiv.length === 0) {
            infoDiv = $('<div id="calculation-info" class="calculation-info"></div>');
            $('#id_amount').parent().append(infoDiv);
        }
        
        infoDiv.html(`
            <div class="alert alert-info">
                <strong>Calculation:</strong> ${numberOfSlots} slots × RM${slotPrice.toFixed(2)} = RM${calculatedAmount.toFixed(2)}
            </div>
        `);
        
        setTimeout(function() {
            infoDiv.fadeOut();
        }, 5000);
    }
    
    // Function to enhance asset dropdown with slot price information
    function enhanceAssetDropdown() {
        var assetSelect = $('#id_asset');
        
        // Add event listener for asset change
        assetSelect.on('change', function() {
            calculateAmount();
            
            // Update slots input placeholder with slot price info
            var selectedOption = $(this).find('option:selected');
            var optionText = selectedOption.text();
            var slotsInput = $('#id_number_of_slots');
            
            if (optionText.includes('slots available')) {
                var slotPriceMatch = optionText.match(/\(.*?(\d+(?:\.\d{2})?)\s*per slot/i);
                if (slotPriceMatch) {
                    var slotPrice = slotPriceMatch[1];
                    slotsInput.attr('placeholder', `Enter number of slots (RM${slotPrice} per slot)`);
                }
            }
        });
    }
    
    // Initialize when document is ready
    $(document).ready(function() {
        // Check if we're on a contribution add/change page
        if ($('#id_asset').length && $('#id_number_of_slots').length) {
            
            // Enhance asset dropdown
            enhanceAssetDropdown();
            
            // Add event listeners for real-time calculation
            $('#id_number_of_slots').on('input change', function() {
                calculateAmount();
            });
            
            // Add auto-calculate button
            var calculateButton = $('<button type="button" class="btn btn-secondary" id="auto-calculate-btn">' +
                '<i class="fas fa-calculator"></i> Auto Calculate Amount</button>');
            
            $('#id_amount').parent().append(calculateButton);
            
            calculateButton.on('click', function() {
                calculateAmount();
                $(this).addClass('btn-success').removeClass('btn-secondary');
                setTimeout(function() {
                    calculateButton.removeClass('btn-success').addClass('btn-secondary');
                }, 1000);
            });
            
            // Add help text
            var helpText = $('<small class="form-text text-muted">' +
                '<i class="fas fa-info-circle"></i> Amount will be automatically calculated based on number of slots and asset slot price.</small>');
            $('#id_amount').parent().append(helpText);
            
            // Add CSS for visual feedback
            $('<style>')
                .prop('type', 'text/css')
                .html(`
                    .calculated-amount {
                        background-color: #d4edda !important;
                        border-color: #c3e6cb !important;
                        transition: all 0.3s ease;
                    }
                    #auto-calculate-btn {
                        margin-left: 10px;
                        margin-top: 5px;
                    }
                    #auto-calculate-btn.btn-success {
                        background-color: #28a745;
                        border-color: #28a745;
                    }
                    .calculation-info {
                        margin-top: 10px;
                    }
                    .calculation-info .alert {
                        padding: 8px 12px;
                        font-size: 0.9em;
                        border-radius: 4px;
                    }
                `)
                .appendTo('head');
        }
        
        // Add bulk calculation functionality to list view
        if ($('.results').length && $('input[name="_selected_action"]').length) {
            var bulkButton = $('<button type="button" class="btn btn-warning" id="bulk-calculate-btn">' +
                '<i class="fas fa-calculator"></i> Bulk Calculate Amounts</button>');
            
            $('.actions').prepend(bulkButton);
            
            bulkButton.on('click', function() {
                var selectedItems = $('input[name="_selected_action"]:checked');
                if (selectedItems.length === 0) {
                    alert('Please select contributions to calculate amounts for.');
                    return;
                }
                
                if (confirm('Calculate amounts for ' + selectedItems.length + ' selected contributions?')) {
                    // Set the action
                    $('#action').val('auto_generate_amounts');
                    $('form#changelist-form').submit();
                }
            });
            
            // Add "Recalculate All" button
            var recalculateAllButton = $('<button type="button" class="btn btn-info" id="recalculate-all-btn">' +
                '<i class="fas fa-sync-alt"></i> Recalculate All Amounts</button>');
            
            $('.actions').prepend(recalculateAllButton);
            
            recalculateAllButton.on('click', function() {
                if (confirm('This will recalculate amounts for ALL contributions in the system. Continue?')) {
                    // Set the action
                    $('#action').val('recalculate_all_amounts');
                    $('form#changelist-form').submit();
                }
            });
        }
        
        // Add quick access button to bulk generate page
        if ($('.results').length) {
            var bulkGenerateButton = $('<a href="/admin/waqaf/contribution/bulk-generate-amounts/" class="btn btn-primary" style="margin-right: 10px;">' +
                '<i class="fas fa-magic"></i> Bulk Generate Amounts</a>');
            
            $('.actions').prepend(bulkGenerateButton);
        }
    });
    
})(django.jQuery);
