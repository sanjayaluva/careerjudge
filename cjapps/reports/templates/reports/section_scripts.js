// Custom filter for placeholder replacement
function replacePlaceholder(text, placeholder, replacement) {
    if (!text || !placeholder || !replacement) return text;
    return text.replace(placeholder, replacement);
}

// Score band manager
class ScoreBandManager {
    constructor(configId) {
        this.configId = configId;
        this.bands = [];
        this.selectedSection = null;
    }
    
    loadBands(sectionId) {
        this.selectedSection = sectionId;
        return $.ajax({
            url: `/reports/configurations/${this.configId}/bands/`,
            method: 'POST',
            headers: {
                'X-CSRFToken': $('input[name="csrfmiddlewaretoken"]').val()
            },
            contentType: 'application/json',
            data: JSON.stringify({
                action: 'get',
                section_id: sectionId
            }),
            success: (response) => {
                if (response.status === 'success') {
                    this.bands = response.bands;
                    return this.bands;
                }
                return [];
            }
        });
    }
    
    saveBand(bandData) {
        const data = {
            section_id: this.selectedSection,
            ...bandData
        };
        
        return $.ajax({
            url: `/reports/configurations/${this.configId}/bands/`,
            method: 'POST',
            headers: {
                'X-CSRFToken': $('input[name="csrfmiddlewaretoken"]').val()
            },
            contentType: 'application/json',
            data: JSON.stringify(data),
            success: (response) => {
                if (response.status === 'success') {
                    // Update local bands data
                    this.loadBands(this.selectedSection);
                    return response;
                }
                throw new Error(response.message || 'Failed to save band');
            }
        });
    }
    
    deleteBand(bandId) {
        return $.ajax({
            url: `/reports/configurations/${this.configId}/bands/`,
            method: 'POST',
            headers: {
                'X-CSRFToken': $('input[name="csrfmiddlewaretoken"]').val()
            },
            contentType: 'application/json',
            data: JSON.stringify({
                action: 'delete',
                band_id: bandId
            }),
            success: (response) => {
                if (response.status === 'success') {
                    // Update local bands data
                    this.loadBands(this.selectedSection);
                    return response;
                }
                throw new Error(response.message || 'Failed to delete band');
            }
        });
    }
    
    validateBands() {
        // Check if bands cover the full range (0-100)
        if (this.bands.length === 0) return false;
        
        // Sort bands by min_range
        const sortedBands = [...this.bands].sort((a, b) => a.min_range - b.min_range);
        
        // Check if first band starts at 0
        if (parseFloat(sortedBands[0].min_range) > 0) return false;
        
        // Check if last band ends at 100
        if (parseFloat(sortedBands[sortedBands.length - 1].max_range) < 100) return false;
        
        // Check for gaps between bands
        for (let i = 0; i < sortedBands.length - 1; i++) {
            if (parseFloat(sortedBands[i].max_range) !== parseFloat(sortedBands[i + 1].min_range)) {
                return false;
            }
        }
        
        return true;
    }
}

// Contrast Variable Manager for typological reports
class ContrastVariableManager {
    constructor(configId) {
        this.configId = configId;
        this.selectedSection = null;
    }
    
    loadContrastVariables(sectionId) {
        this.selectedSection = sectionId;
        return $.ajax({
            url: `/reports/configurations/${this.configId}/contrast-variables/`,
            method: 'POST',
            headers: {
                'X-CSRFToken': $('input[name="csrfmiddlewaretoken"]').val()
            },
            contentType: 'application/json',
            data: JSON.stringify({
                action: 'get',
                section_id: sectionId
            }),
            success: (response) => {
                if (response.status === 'success') {
                    return response.contrast_variable;
                }
                return null;
            }
        });
    }
    
    saveContrastVariables(cvData) {
        const data = {
            section_id: this.selectedSection,
            ...cvData
        };
        
        return $.ajax({
            url: `/reports/configurations/${this.configId}/contrast-variables/`,
            method: 'POST',
            headers: {
                'X-CSRFToken': $('input[name="csrfmiddlewaretoken"]').val()
            },
            contentType: 'application/json',
            data: JSON.stringify(data),
            success: (response) => {
                if (response.status === 'success') {
                    return response;
                }
                throw new Error(response.message || 'Failed to save contrast variables');
            }
        });
    }
    
    validateContrastRules(rule) {
        // Basic validation of calculation rules
        try {
            // Test with a sample score
            const ss = 50; // Sample section score
            eval(rule);
            return true;
        } catch (e) {
            return false;
        }
    }
}
