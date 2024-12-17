// Description: This file contains the JavaScript code for handling different types of questions in the quiz.

class BaseHandler {
    collectAnswer() {
        return null;
    }

    isAnswered() {
        return false;
    }
}

class MCQHandler {
    collectAnswer() {
        const selectedOption = document.querySelector('input[name="answer"]:checked');
        return {
            selected_option: selectedOption ? selectedOption.value : null
        };
    }

    isAnswered() {
        return !!document.querySelector('input[name="answer"]:checked');
    }
}

class FIBHandler {
    collectAnswer() {
        const inputs = document.querySelectorAll('.fib-input');
        return {
            answers: Array.from(inputs).map(input => input.value.trim())
        };
    }

    isAnswered() {
        const inputs = document.querySelectorAll('.fib-input');
        return Array.from(inputs).every(input => input.value.trim() !== '');
    }
}

class HotspotHandler {
    constructor() {
        this.initHotspot();
    }

    initHotspot() {
        const overlay = document.getElementById('hotspotOverlay');
        const input = document.getElementById('hotspotCoordinates');

        overlay.addEventListener('click', (e) => {
            const rect = overlay.getBoundingClientRect();
            const x = ((e.clientX - rect.left) / rect.width * 100).toFixed(2);
            const y = ((e.clientY - rect.top) / rect.height * 100).toFixed(2);
            
            this.clearMarkers();
            this.createMarker(x, y);
            input.value = `${x},${y}`;
        });
    }

    clearMarkers() {
        const markers = document.querySelectorAll('.hotspot-marker');
        markers.forEach(marker => marker.remove());
    }

    createMarker(x, y) {
        const marker = document.createElement('div');
        marker.className = 'hotspot-marker';
        marker.style.left = `${x}%`;
        marker.style.top = `${y}%`;
        document.getElementById('hotspotOverlay').appendChild(marker);
    }

    collectAnswer() {
        const coordinates = document.getElementById('hotspotCoordinates').value;
        return coordinates ? {
            coordinates: coordinates.split(',').map(Number)
        } : null;
    }

    isAnswered() {
        return !!document.getElementById('hotspotCoordinates').value;
    }
}


class MatchHandler {
    constructor() {
        this.initDragDrop();
    }

    initDragDrop() {
        const items = document.querySelectorAll('.match-item');
        const dropzones = document.querySelectorAll('.match-dropzone');

        items.forEach(item => {
            item.addEventListener('dragstart', this.handleDragStart);
            item.addEventListener('dragend', this.handleDragEnd);
        });

        dropzones.forEach(dropzone => {
            dropzone.addEventListener('dragover', this.handleDragOver);
            dropzone.addEventListener('drop', this.handleDrop);
        });
    }

    collectAnswer() {
        const matches = {};
        document.querySelectorAll('.match-dropzone').forEach(dropzone => {
            const droppedItem = dropzone.querySelector('.match-item');
            if (droppedItem) {
                matches[dropzone.dataset.itemId] = droppedItem.dataset.itemId;
            }
        });
        return { matches };
    }

    isAnswered() {
        const dropzones = document.querySelectorAll('.match-dropzone');
        return Array.from(dropzones).every(zone => zone.querySelector('.match-item'));
    }
}

class PsyRatingHandler {
    collectAnswer() {
        const selectedRating = document.querySelector('input[name="rating"]:checked');
        return {
            rating: selectedRating ? parseInt(selectedRating.value) : null
        };
    }

    isAnswered() {
        return !!document.querySelector('input[name="rating"]:checked');
    }
}

class VideoHandler extends MCQHandler {
    constructor() {
        super();
        this.initVideoTracking();
    }

    initVideoTracking() {
        const video = document.getElementById('questionVideo');
        if (video) {
            video.addEventListener('ended', () => {
                this.videoWatched = true;
            });
        }
    }

    isAnswered() {
        return super.isAnswered() && this.videoWatched;
    }
}

class RankingHandler {
    constructor() {
        this.initRankingValidation();
    }

    initRankingValidation() {
        document.querySelectorAll('.rank-select').forEach(select => {
            select.addEventListener('change', () => this.validateRankings());
        });
    }

    validateRankings() {
        const selects = document.querySelectorAll('.rank-select');
        const selectedRanks = new Set();
        
        selects.forEach(select => {
            const value = select.value;
            if (value) {
                if (selectedRanks.has(value)) {
                    select.value = '';
                    alert('Each rank can only be used once');
                } else {
                    selectedRanks.add(value);
                }
            }
        });
    }

    collectAnswer() {
        const rankings = {};
        document.querySelectorAll('.ranking-statement').forEach(statement => {
            const text = statement.querySelector('.statement-text').textContent;
            const rank = statement.querySelector('.rank-select').value;
            if (rank) {
                rankings[text] = parseInt(rank);
            }
        });
        return { rankings };
    }

    isAnswered() {
        const selects = document.querySelectorAll('.rank-select');
        return Array.from(selects).every(select => select.value !== '');
    }
}


class GridHandler {
    constructor() {
        this.initGridEvents();
        this.selectedCell = null;
    }

    initGridEvents() {
        document.querySelectorAll('.grid-cell').forEach(cell => {
            cell.addEventListener('click', () => this.showPopup(cell));
        });

        document.querySelector('.close-popup').addEventListener('click', () => {
            document.getElementById('gridPopup').style.display = 'none';
        });

        document.getElementById('selectOption').addEventListener('click', () => {
            if (this.selectedCell) {
                this.selectCell(this.selectedCell);
            }
            document.getElementById('gridPopup').style.display = 'none';
        });
    }

    showPopup(cell) {
        const popup = document.getElementById('gridPopup');
        const content = document.getElementById('popupContent');
        this.selectedCell = cell;

        if (cell.dataset.contentType === 'text') {
            content.innerHTML = cell.dataset.content;
        } else {
            content.innerHTML = `<img src="${cell.dataset.content}" alt="Option" style="max-width: 100%">`;
        }

        popup.style.display = 'block';
    }

    selectCell(cell) {
        document.querySelectorAll('.grid-cell').forEach(c => c.classList.remove('selected'));
        cell.classList.add('selected');
    }

    collectAnswer() {
        const selectedCell = document.querySelector('.grid-cell.selected');
        return selectedCell ? {
            selected_cell: selectedCell.dataset.cellId
        } : null;
    }

    isAnswered() {
        return !!document.querySelector('.grid-cell.selected');
    }
}



class QuestionTypeHandler {
    static handlers = {
        mcq_text: new MCQHandler(),
        mcq_image: new MCQHandler(),
        fib_text: new FIBHandler(),
        cus_hotspot_single: new HotspotHandler(),
        // Add other handlers
        cus_match: new MatchHandler(),
        psy_rating: new PsyRatingHandler(),
        mcq_video: new VideoHandler(),
        psy_ranking: new RankingHandler(),
        cus_grid: new GridHandler()
    };

    static getHandler(questionType) {
        return this.handlers[questionType] || new BaseHandler();
    }
}


// // Update QuestionTypeHandler
// QuestionTypeHandler.handlers = {
//     ...QuestionTypeHandler.handlers,
//     mcq_video: new VideoHandler(),
//     psy_ranking: new RankingHandler(),
//     cus_grid: new GridHandler()
// };
