$(document).ready(function() {
    // Initialize rich text editors
    $('.rich-text-editor').each(function() {
        CKEDITOR.replace(this);
    });

    // Show/hide question type fields based on selected type
    $('#id_question_type').change(function() {
        var questionType = $(this).val();
        $('.question-type-fields > div').hide();
        if (questionType.startsWith('MCQ')) {
            $('#mcq-fields').show();
        } else if (questionType === 'MCQ_HOTSPOT') {
            $('#hotspot-fields').show();
        } else if (questionType.endsWith('FLASH')) {
            $('#flash-fields').show();
        } else if (questionType === 'MATCH') {
            $('#matching-fields').show();
        }
        updatePreview();
    });

    // Trigger change event on page load
    $('#id_question_type').trigger('change');

    // MCQ options
    $('#add-option').click(function() {
        var form_idx = $('#id_options-TOTAL_FORMS').val();
        var newForm = $('#options-list .option-form:first').clone(true);
        newForm.find(':input').each(function() {
            var name = $(this).attr('name').replace('-0-', '-' + form_idx + '-');
            var id = 'id_' + name;
            $(this).attr({'name': name, 'id': id}).val('').removeAttr('checked');
        });
        newForm.find('.rich-text-editor').each(function() {
            $(this).removeClass('cke_editable');
            $(this).removeAttr('id');
        });
        newForm.insertBefore($(this));
        $('#id_options-TOTAL_FORMS').val(parseInt(form_idx) + 1);
        CKEDITOR.replace(newForm.find('.rich-text-editor')[0]);
        updatePreview();
    });

    // Hotspot
    var canvas = document.getElementById('hotspot-canvas');
    var ctx = canvas.getContext('2d');
    var isDrawing = false;
    var startX, startY;

    $('#hotspot-image').on('load', function() {
        canvas.width = this.width;
        canvas.height = this.height;
    });

    canvas.addEventListener('mousedown', startDrawing);
    canvas.addEventListener('mousemove', draw);
    canvas.addEventListener('mouseup', stopDrawing);

    function startDrawing(e) {
        isDrawing = true;
        [startX, startY] = [e.offsetX, e.offsetY];
    }

    function draw(e) {
        if (!isDrawing) return;
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.strokeRect(startX, startY, e.offsetX - startX, e.offsetY - startY);
    }

    function stopDrawing(e) {
        if (!isDrawing) return;
        isDrawing = false;
        var form_idx = $('#id_hotspots-TOTAL_FORMS').val();
        var newForm = $('#hotspots-list .hotspot-form:first').clone(true);
        newForm.find(':input').each(function() {
            var name = $(this).attr('name').replace('-0-', '-' + form_idx + '-');
            var id = 'id_' + name;
            $(this).attr({'name': name, 'id': id}).val('').removeAttr('checked');
        });
        newForm.find('[name$="-x"]').val(startX);
        newForm.find('[name$="-y"]').val(startY);
        newForm.find('[name$="-width"]').val(e.offsetX - startX);
        newForm.find('[name$="-height"]').val(e.offsetY - startY);
        newForm.insertBefore($('#add-hotspot'));
        $('#id_hotspots-TOTAL_FORMS').val(parseInt(form_idx) + 1);
        updatePreview();
    }

    // Flash cards
    $('#add-flash-card').click(function() {
        var form_idx = $('#id_flash_cards-TOTAL_FORMS').val();
        var newForm = $('#flash-cards-list .flash-card-form:first').clone(true);
        newForm.find(':input').each(function() {
            var name = $(this).attr('name').replace('-0-', '-' + form_idx + '-');
            var id = 'id_' + name;
            $(this).attr({'name': name, 'id': id}).val('').removeAttr('checked');
        });
        newForm.find('.rich-text-editor').each(function() {
            $(this).removeClass('cke_editable');
            $(this).removeAttr('id');
        });
        newForm.insertBefore($(this));
        $('#id_flash_cards-TOTAL_FORMS').val(parseInt(form_idx) + 1);
        CKEDITOR.replace(newForm.find('.rich-text-editor')[0]);
        updatePreview();
    });

    // Matching pairs
    $('#add-matching-pair').click(function() {
        var form_idx = $('#id_matching_pairs-TOTAL_FORMS').val();
        var newForm = $('#matching-pairs-list .matching-pair-form:first').clone(true);
        newForm.find(':input').each(function() {
            var name = $(this).attr('name').replace('-0-', '-' + form_idx + '-');
            var id = 'id_' + name;
            $(this).attr({'name': name, 'id': id}).val('').removeAttr('checked');
        });
        newForm.insertBefore($(this));
        $('#id_matching_pairs-TOTAL_FORMS').val(parseInt(form_idx) + 1);
        updatePreview();
    });

    // Media
    $('#add-media').click(function() {
        var form_idx = $('#id_media-TOTAL_FORMS').val();
        var newForm = $('#media-list .media-form:first').clone(true);
        newForm.find(':input').each(function() {
            var name = $(this).attr('name').replace('-0-', '-' + form_idx + '-');
            var id = 'id_' + name;
            $(this).attr({'name': name, 'id': id}).val('').removeAttr('checked');
        });
        newForm.insertBefore($(this));
        $('#id_media-TOTAL_FORMS').val(parseInt(form_idx) + 1);
        updatePreview();
    });

    // Live preview
    function updatePreview() {
        var questionType = $('#id_question_type').val();
        var title = $('#id_title').val();
        var content = CKEDITOR.instances['id_content'].getData();
        var previewHtml = '<h4>' + title + '</h4><p>' + content + '</p>';

        if (questionType.startsWith('MCQ')) {
            previewHtml += '<ul>';
            $('#options-list .option-form').each(function() {
                var optionContent = CKEDITOR.instances[$(this).find('.rich-text-editor').attr('id')].getData();
                var isCorrect = $(this).find('[name$="-is_correct"]').is(':checked');
                previewHtml += '<li>' + optionContent + (isCorrect ? ' (Correct)' : '') + '</li>';
            });
            previewHtml += '</ul>';
        } else if (questionType === 'MCQ_HOTSPOT') {
            previewHtml += '<img src="' + $('#hotspot-image').attr('src') + '" alt="Hotspot Image">';
        } else if (questionType.endsWith('FLASH')) {
            previewHtml += '<div class="flash-cards">';
            $('#flash-cards-list .flash-card-form').each(function() {
                var cardContent = CKEDITOR.instances[$(this).find('.rich-text-editor').attr('id')].getData();
                previewHtml += '<div class="flash-card">' + cardContent + '</div>';
            });
            previewHtml += '</div>';
        } else if (questionType === 'MATCH') {
            previewHtml += '<div class="matching-pairs">';
            $('#matching-pairs-list .matching-pair-form').each(function() {
                var leftItem = $(this).find('[name$="-left_item"]').val();
                var rightItem = $(this).find('[name$="-right_item"]').val();
                previewHtml += '<div class="matching-pair"><span>' + leftItem + '</span> - <span>' + rightItem + '</span></div>';
            });
            previewHtml += '</div>';
        }

        $('#preview-content').html(previewHtml);
    }

    // Update preview on input change
    $(document).on('input', ':input', updatePreview);
    $(document).on('change', ':input', updatePreview);
    for (var i in CKEDITOR.instances) {
        CKEDITOR.instances[i].on('change', updatePreview);
    }

    // Initial preview update
    updatePreview();
});
