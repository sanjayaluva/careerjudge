// Description: This file contains the JavaScript code for handling different types of questions in the quiz.

class BaseHandler {
    constructor() {
        // if (BaseHandler.instance) {
        //     return BaseHandler.instance;
        // }
        // BaseHandler.instance = this;
    }

    init() {
        // Default initialization method
    }

    cleanup() {
        // Default cleanup method
        let elem = document.querySelector('#question-wrapper');
        elem.replaceWith(elem.cloneNode(true));
    }

    reinit() {
        // Default reinitialization method
        this.init?.();
    }

    collectAnswer() {
        return null;
    }

    isAnswered() {
        return false;
    }
}

class MCQHandler extends BaseHandler {
    constructor() {
        super();
        // if (MCQHandler.instance) {
        //     return MCQHandler.instance;
        // }
        // MCQHandler.instance = this;
    }

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

class FIBHandler extends BaseHandler {
    constructor() {
        super();
        this.init();
    }

    init() {
        this.attachEventListeners();
    }

    attachEventListeners() {
        document.querySelectorAll('.fib-input').forEach(input => {
            input.addEventListener('input', () => this.handleInput(input));
            input.addEventListener('blur', () => this.saveAnswer());
        });
    }

    handleInput(input) {
        // Optional: Add input formatting or restrictions here
        input.value = input.value.trim();
    }

    saveAnswer() {
        // Save answer via AssessmentManager
        if (typeof window.assessmentManager !== 'undefined') {
            window.assessmentManager.saveCurrentAnswer();
        }
    }

    collectAnswer() {
        const answers = [];
        document.querySelectorAll('.fib-input').forEach(input => {
            answers.push(input.value.trim());
        });
        return { answers };
    }

    isAnswered() {
        const inputs = document.querySelectorAll('.fib-input');
        return Array.from(inputs).every(input => input.value.trim() !== '');
    }
}

class FIBAudioHandler extends FIBHandler {
    constructor() {
        super();
        this.audioPlayed = false;
        this.initAudioTracking();
    }

    initAudioTracking() {
        const audio = document.getElementById('questionAudio');
        if (audio) {
            audio.addEventListener('ended', () => {
                this.audioPlayed = true;
            });
        }
    }

    isAnswered() {
        return super.isAnswered() && this.audioPlayed;
    }
}

class FIBVideoHandler extends FIBHandler {
    constructor() {
        super();
        this.videoWatched = false;
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

class FIBParagraphHandler extends FIBHandler {
    constructor() {
        super();
        this.paragraphRead = false;
        this.timer = null;
        this.init();
    }

    init() {
        this.initParagraphTimer();
        super.init();
    }

    initParagraphTimer() {
        const container = document.querySelector('.paragraph-container');
        if (!container) return;

        const paragraphContent = container.querySelector('.paragraph-content');
        const questionContent = container.querySelector('.question-content');
        const timeDisplay = container.querySelector('.time-display');
        
        let timeLeft = parseInt(container.dataset.interval);
        if (isNaN(timeLeft)) return;

        timeDisplay.textContent = `Time remaining: ${timeLeft} seconds`;

        this.timer = setInterval(() => {
            timeLeft--;
            timeDisplay.textContent = `Time remaining: ${timeLeft} seconds`;
            
            if (timeLeft <= 0) {
                clearInterval(this.timer);
                paragraphContent.classList.add('d-none');
                questionContent.classList.remove('d-none');
                this.paragraphRead = true;
            }
        }, 1000);
    }

    cleanup() {
        if (this.timer) {
            clearInterval(this.timer);
        }
        super.cleanup();
    }

    isAnswered() {
        return super.isAnswered() && this.paragraphRead;
    }
}

class FIBFlashHandler extends FIBHandler {
    constructor() {
        super();
        this.items = [];
        this.currentIndex = 0;
        this.interval = null;
        this.flashContent = null;
        this.flashCounter = null;
        this.optionsContainer = null;
        this.flashInterval = null;
        this.flashSequenceComplete = false;
        this.initFlash();
        // this.init();
    }

    initFlash() {
        const container = document.querySelector('.flash-question-container');
        if (!container) return;
        
        const itemsScript = document.getElementById('flash-items');
        if (!itemsScript) return;
        
        this.items = JSON.parse(itemsScript.textContent);
        this.flashInterval = parseInt(container.dataset.interval) * 1000;
        this.flashContent = container.querySelector('.flash-content');
        this.flashCounter = container.querySelector('.flash-counter');
        this.optionsContainer = container.querySelector('.flash-options');

        this.attachEventListeners();
        this.showNextItem();
        // super.init(); // Call FIBHandler's init after flash setup
    }

    showNextItem() {
        if (this.currentIndex < this.items.length) {
            this.showItem(this.currentIndex);
            setTimeout(() => {
                this.currentIndex++;
                this.showNextItem();
            }, this.flashInterval);
        } else {
            this.endFlashSequence();
        }
    }

    showItem(index) {
        const item = this.items[index];
        this.flashCounter.textContent = `Item ${index + 1} of ${this.items.length}`;
        
        if (item.image) {
            this.flashContent.innerHTML = `<img src="${item.image}" alt="Flash item ${index + 1}" class="flash-image img-fluid">`;
        } else {
            this.flashContent.innerHTML = `<div class="flash-text h3 text-center">${item.text}</div>`;
        }
    }

    endFlashSequence() {
        clearInterval(this.interval);
        // this.flashContent.innerHTML = '';
        this.flashContent.classList.add('d-none');
        this.flashCounter.textContent = 'Sequence complete';
        this.optionsContainer.classList.remove('d-none');
        this.flashSequenceComplete = true;
    }

    cleanup() {
        if (this.interval) {
            clearInterval(this.interval);
        }
        super.cleanup();
    }

    collectAnswer() {
        const answers = [];
        document.querySelectorAll('.fib-input').forEach(input => {
            answers.push({
                index: parseInt(input.dataset.index),
                answer: input.value.trim()
            });
        });
        return { answers };
    }

    isAnswered() {
        return this.flashSequenceComplete && 
               document.querySelectorAll('.fib-input').length > 0 && 
               Array.from(document.querySelectorAll('.fib-input')).every(input => input.value.trim() !== '');
    }
}


class HotspotHandler extends BaseHandler {
    constructor() {
        super();
        this.canvas = null;
        this.selectedShapes = new Set();
        this.resizeHandler = this.handleResize.bind(this);
        this.questionType = document.querySelector('#question-wrapper')?.dataset.questionType;
        this.init();
        // this.canvas = null;
        // this.selectedShapes = new Set();
        // this.questionType = document.querySelector('#question-wrapper').dataset.questionType;
        // this.init();
        // this.setupResizeHandler();
    }
    
    handleResize() {
        if (this.canvas) {
            this.loadImage();
        }
    }

    init() {
        const container = document.querySelector('.hotspot-container');
        if (!container) return;

        // Set initial container width to parent element width
        // container.style.width = container.parentElement.offsetWidth + 'px';

        this.canvas = new fabric.Canvas('hotspot-canvas', {
            selection: false,
            hoverCursor: 'pointer'
        });

        this.loadImage();
        this.resizeCanvas();
        this.setupResizeHandler();
    }

    cleanup() {
        window.removeEventListener('resize', this.resizeHandler);
        
        if (this.canvas) {
            this.canvas.dispose();
            this.canvas = null;
        }
        
        if (this.selectedShapes) {
            this.selectedShapes = new Set();
        }
        
        let elem = document.querySelector('#question-wrapper');
        elem.replaceWith(elem.cloneNode(true));
    }

    reinit() {
        this.cleanup();
        this.canvas = null;
        this.selectedShapes = new Set();
        this.questionType = document.querySelector('#question-wrapper').dataset.questionType;
        this.init();
        this.setupResizeHandler();
    }

    setupResizeHandler() {
        window.addEventListener('resize', this.resizeHandler);
    }
    // setupResizeHandler() {
    //     window.addEventListener('resize', () => { 
    //         // Clear all objects from canvas
    //         this.canvas.clear();
    //         // Reload image and shapes with new dimensions
    //         this.loadImage();
    //         // this.resizeCanvas() 
    //     });
    // }

    // resizeCanvas() {
    //     // const container = document.querySelector('.hotspot-container');
    //     // const canvas = document.getElementById('hotspot-canvas');
    //     // const containerWidth = container.offsetWidth;
        
    //     // const scale = containerWidth / canvas.width;
    //     // canvas.style.width = containerWidth + 'px';
    //     // canvas.style.height = (canvas.height * scale) + 'px';
    //     const container = document.querySelector('.hotspot-container');
    //     const containerWidth = container.offsetWidth;
        
    //     if (this.canvas) {
    //         const currentImage = this.canvas.backgroundImage;
    //         if (currentImage) {
    //             const scale = containerWidth / currentImage.width;
    //             const scaledHeight = currentImage.height * scale;

    //             this.canvas.setDimensions({
    //                 width: containerWidth,
    //                 height: scaledHeight
    //             });

    //             currentImage.set({
    //                 scaleX: scale,
    //                 scaleY: scale,
    //                 originX: 'left',
    //                 originY: 'top'
    //             });

    //             this.canvas.renderAll();
    //         }
    //     }
    // }

    resizeCanvas() {
        const container = document.querySelector('.hotspot-container');
        const containerWidth = container.offsetWidth;
        
        if (this.canvas) {
            const currentImage = this.canvas.backgroundImage;
            if (currentImage) {
                const scale = containerWidth / currentImage.width;
                const scaledHeight = currentImage.height * scale;

                this.canvas.setDimensions({
                    width: containerWidth,
                    height: scaledHeight
                });

                currentImage.set({
                    scaleX: scale,
                    scaleY: scale,
                    originX: 'left',
                    originY: 'top'
                });

                // Scale all shapes
                this.canvas.getObjects().forEach(obj => {
                    obj.set({
                        left: obj.left * scale,
                        top: obj.top * scale,
                        scaleX: scale,
                        scaleY: scale
                    });
                    if (obj.type === 'circle') {
                        obj.set({
                            radius: obj.radius * scale
                        });
                    }
                });

                this.canvas.renderAll();
            }
        }
    }

    loadShapes() {
        const shapesData = JSON.parse(document.getElementById('hotspot-data').textContent);
        if (!shapesData) return;

        const canvasWidth = this.canvas.width;
        const canvasHeight = this.canvas.height;

        shapesData.forEach((shapeData, index) => {
            let shape;
            const left = (shapeData.left * canvasWidth) / 100;
            const top = (shapeData.top * canvasHeight) / 100;

            const commonProps = {
                left: left,
                top: top,
                selectable: false,
                hoverCursor: 'pointer'
            };

            if (shapeData.type === 'rect') {
                shape = new fabric.Rect({
                    ...commonProps,
                    width: (shapeData.width * canvasWidth) / 100,
                    height: (shapeData.height * canvasHeight) / 100,
                    fill: 'rgba(255,0,0,0.1)',
                    stroke: 'red',
                    strokeWidth: 2
                });
            } else if (shapeData.type === 'circle') {
                shape = new fabric.Circle({
                    ...commonProps,
                    radius: (shapeData.radius * canvasWidth) / 100,
                    fill: 'rgba(0,0,255,0.1)',
                    stroke: 'blue',
                    strokeWidth: 2
                });
            } else if (shapeData.type === 'polygon') {
                const points = shapeData.points.map(point => ({
                    x: (point.x * canvasWidth) / 100,
                    y: (point.y * canvasHeight) / 100
                }));
                shape = new fabric.Polygon(points, {
                    ...commonProps,
                    fill: 'rgba(0,255,0,0.1)',
                    stroke: 'green',
                    strokeWidth: 2
                });
            }

            if (shape) {
                shape.shapeId = index + 1;
                this.canvas.add(shape);
            }
        });

        this.canvas.renderAll();
    }

    loadImage() {
        const imageElement = document.querySelector('#hotspotImage');
        if (!imageElement || !this.canvas) return;

        fabric.Image.fromURL(imageElement.src, (img) => {
            if (!this.canvas) return;
            
            const containerWidth = $('.canvas-container')?.parent().width() || 800;
            const scale = containerWidth / img.width;
            const scaledHeight = img.height * scale;

            this.canvas.setDimensions({
                width: containerWidth,
                height: scaledHeight
            });

            img.set({
                selectable: false,
                evented: false,
                scaleX: scale,
                scaleY: scale,
                originX: 'left',
                originY: 'top'
            });

            this.canvas.setBackgroundImage(img, this.canvas.renderAll.bind(this.canvas));
            this.loadShapes();
            this.bindEvents();
        });
    }

    // loadShapes() {
    //     const shapesData = JSON.parse(document.getElementById('hotspot-data').textContent);
    //     if (!shapesData) return;

    //     const canvasWidth = this.canvas.width;
    //     const canvasHeight = this.canvas.height;

    //     shapesData.forEach((shapeData, index) => {
    //         let shape;
    //         const left = (shapeData.left * canvasWidth) / 100;
    //         const top = (shapeData.top * canvasHeight) / 100;

    //         const commonProps = {
    //             left: shapeData.left,//left,
    //             top: shapeData.top,//top,
    //             selectable: false,
    //             hoverCursor: 'pointer'
    //         };

    //         if (shapeData.type === 'rect') {
    //             shape = new fabric.Rect({
    //                 ...commonProps,
    //                 width: shapeData.width,//(shapeData.width * canvasWidth) / 100,
    //                 height: shapeData.height,//(shapeData.height * canvasHeight) / 100,
    //                 fill: 'rgba(255,0,0,0.1)',
    //                 stroke: 'red',
    //                 strokeWidth: 2
    //             });
    //         } else if (shapeData.type === 'circle') {
    //             shape = new fabric.Circle({
    //                 ...commonProps,
    //                 radius: shapeData.radius,//(shapeData.radius * canvasWidth) / 100,
    //                 fill: 'rgba(0,0,255,0.1)',
    //                 stroke: 'blue',
    //                 strokeWidth: 2
    //             });
    //         } else if (shapeData.type === 'polygon') {
    //             const points = shapeData.points.map(point => ({
    //                 x: point.x,//(point.x * canvasWidth) / 100,
    //                 y: point.y,//(point.y * canvasHeight) / 100
    //             }));
    //             shape = new fabric.Polygon(points, {
    //                 ...commonProps,
    //                 fill: 'rgba(0,255,0,0.1)',
    //                 stroke: 'green',
    //                 strokeWidth: 2
    //             });
    //         }

    //         if (shape) {
    //             shape.shapeId = index + 1; // 1-based index for shape IDs
    //             this.canvas.add(shape);
    //         }
    //     });

    //     this.canvas.renderAll();
    // }

    bindEvents() {
        this.canvas.on('mouse:down', (opt) => {
            const clickedShape = opt.target;
            if (!clickedShape) return;

            if (this.questionType === 'cus_hotspot_single') {
                this.handleSingleSelection(clickedShape);
            } else {
                this.handleMultipleSelection(clickedShape);
            }
            
            this.canvas.renderAll();
        });

        window.addEventListener('resize', () => {
            this.loadImage();
        });
    }

    handleSingleSelection(shape) {
        // Clear previous selection
        this.canvas.getObjects().forEach(obj => {
            obj.set({
                opacity: 1,
                fill: this.getDefaultFill(obj.type)
            });
        });
        this.selectedShapes.clear();

        // Set new selection
        shape.set({
            opacity: 0.7,
            fill: 'rgba(255,255,0,0.2)'
        });
        this.selectedShapes.add(shape.shapeId);
        this.updateHiddenField();
    }

    handleMultipleSelection(shape) {
        if (this.selectedShapes.has(shape.shapeId)) {
            // Deselect
            shape.set({
                opacity: 1,
                fill: this.getDefaultFill(shape.type)
            });
            this.selectedShapes.delete(shape.shapeId);
        } else {
            // Select
            shape.set({
                opacity: 0.7,
                fill: 'rgba(255,255,0,0.2)'
            });
            this.selectedShapes.add(shape.shapeId);
        }
        this.updateHiddenField();
    }

    updateHiddenField() {
        const hiddenInput = document.getElementById('selectedShape');
        hiddenInput.value = JSON.stringify(Array.from(this.selectedShapes));
    }

    getDefaultFill(type) {
        switch(type) {
            case 'rect': return 'rgba(255,0,0,0.1)';
            case 'circle': return 'rgba(0,0,255,0.1)';
            case 'polygon': return 'rgba(0,255,0,0.1)';
            default: return 'rgba(255,0,0,0.1)';
        }
    }

    // collectAnswer() {
    //     return {
    //         type: 'hotspot',
    //         value: Array.from(this.selectedShapes),
    //         valid: this.selectedShapes.size > 0
    //     };
    // }

    // static collectAnswers() {
    //     const handler = window.hotspotHandler;
    //     return handler.collectAnswer();
    // }

    collectAnswer() {
        const selectedShapesArray = Array.from(this.selectedShapes);
        return {
            type: 'hotspot',
            value: selectedShapesArray,
            valid: selectedShapesArray.length > 0
        };
    }

    isAnswered() {
        return this.selectedShapes.size > 0;
    }
}

class PsyRatingHandler {
    constructor() {
        // super();

        // if (PsyRatingHandler.instance) {
        //     return PsyRatingHandler.instance;
        // }
        // PsyRatingHandler.instance = this;
    }

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
        // if (VideoHandler.instance) {
        //     return VideoHandler.instance;
        // }
        // VideoHandler.instance = this;

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

class AudioHandler extends MCQHandler {
    constructor() {
        super();

        this.initAudioTracking();
    }

    initAudioTracking() {
        const audio = document.getElementById('questionAudio');
        if (audio) {
            audio.addEventListener('ended', () => {
                this.audioPlayed = true;
            });
        }
    }

    isAnswered() {
        return super.isAnswered() && this.audioPlayed;
    }
}

class RankingHandler {
    constructor() {
        this.init();
    }

    init() {
        if (document.querySelector('.rank-select')) {
            this.initRankingValidation();
        }
    }

    initRankingValidation() {
        document.querySelectorAll('.rank-select').forEach(select => {
            select.addEventListener('change', this.handleRankChange.bind(this));
        });
    }

    handleRankChange(event) {
        const selects = document.querySelectorAll('.rank-select');
        const selectedRanks = {};
        
        selects.forEach(select => {
            const value = select.value;
            const groupId = select.dataset.groupId;
            
            if (value) {
                if (!selectedRanks[groupId]) {
                    selectedRanks[groupId] = new Set();
                }
                
                if (selectedRanks[groupId].has(value)) {
                    select.value = '';
                    alert(`Each rank can only be used once in group ${groupId}`);
                } else {
                    selectedRanks[groupId].add(value);
                }
            }
        });
    }
    // handleRankChange(event) {
    //     const selects = document.querySelectorAll('.rank-select');
    //     const selectedRanks = new Set();
        
    //     selects.forEach(select => {
    //         const value = select.value;
    //         if (value) {
    //             if (selectedRanks.has(value)) {
    //                 select.value = '';
    //                 alert('Each rank can only be used once');
    //             } else {
    //                 selectedRanks.add(value);
    //             }
    //         }
    //     });
    // }

    cleanup() {
        let elem = document.querySelector('#question-wrapper');
        elem.replaceWith(elem.cloneNode(true));

        // document.querySelectorAll('.rank-select').forEach(select => {
        //     select.removeEventListener('change', this.validateRankings);
        // });
    }

    reinit() {
        this.init();
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

    // collectAnswer() {
    //     const rankings = {};
    //     document.querySelectorAll('.ranking-statement').forEach(statement => {
    //         const text = statement.querySelector('.statement-text').textContent;
    //         const rank = statement.querySelector('.rank-select').value;
    //         if (rank) {
    //             rankings[text] = parseInt(rank);
    //         }
    //     });
    //     return { rankings };
    // }

    // isAnswered() {
    //     const selects = document.querySelectorAll('.rank-select');
    //     return Array.from(selects).every(select => select.value !== '');
    // }
}

class MCQMixedHandler extends MCQHandler {
    // Inherits collectAnswer() and isAnswered() from MCQHandler
    // since the core functionality is the same for radio button selection
}

class MatchHandler {
    constructor() {
        // super();
        // if (MatchHandler.instance) {
        //     return MatchHandler.instance;
        // }
        // MatchHandler.instance = this;

        this.handleDragStart = this.handleDragStart.bind(this);
        this.handleDragOver = this.handleDragOver.bind(this);
        this.handleDrop = this.handleDrop.bind(this);
        this.handleResetMatches = this.handleResetMatches.bind(this);

        // this.draggedItem = null;
        // this.handleRankChange = (event) => this.validateRankings(event);
        this.init();
    }
    
    init() {
        this.initDragDropEvents();
        // if (document.querySelector('.rank-select')) {
        //     this.initRankingValidation();
        // }
    }

    // initRankingValidation() {
    //     document.querySelectorAll('.rank-select').forEach(select => {
    //         select.addEventListener('change', this.handleRankChange);
    //     });
    // }

    cleanup() {
        let elem = document.querySelector('#question-wrapper');
        elem.replaceWith(elem.cloneNode(true));

        // const items = document.querySelectorAll('.match-item');
        // const dropzones = document.querySelectorAll('.match-dropzone');

        // items.forEach(item => {
        //     item.removeEventListener('dragstart', this.handleDragStart);
        //     item.removeEventListener('dragend', this.handleDragEnd);
        // });

        // dropzones.forEach(dropzone => {
        //     dropzone.removeEventListener('dragover', this.handleDragOver);
        //     dropzone.removeEventListener('dragleave', this.handleDragLeave);
        //     dropzone.removeEventListener('drop', this.handleDrop);
        // });
    }

    reinit() {
        this.init();
    }

    initDragDropEvents() {
        const items = document.querySelectorAll('.match-item');
        const dropzones = document.querySelectorAll('.match-dropzone');

        items.forEach(item => {
            item.addEventListener('dragstart', this.handleDragStart);
            item.addEventListener('dragend', this.handleDragEnd);
        });

        dropzones.forEach(dropzone => {
            dropzone.addEventListener('dragover', this.handleDragOver);
            dropzone.addEventListener('dragleave', this.handleDragLeave);
            dropzone.addEventListener('drop', this.handleDrop);
        });

        const resetButton = document.getElementById('reset-matches');
        if (resetButton) {
            resetButton.addEventListener('click', this.handleResetMatches);
        }

        // const items = document.querySelectorAll('.match-item');
        // const dropzones = document.querySelectorAll('.match-dropzone');

        // items.forEach(item => {
        //     item.addEventListener('dragstart', (e) => this.handleDragStart(e));
        //     item.addEventListener('dragend', (e) => this.handleDragEnd(e));
        // });

        // dropzones.forEach(dropzone => {
        //     dropzone.addEventListener('dragover', (e) => this.handleDragOver(e));
        //     dropzone.addEventListener('dragleave', (e) => this.handleDragLeave(e));
        //     dropzone.addEventListener('drop', (e) => this.handleDrop(e));
        // });

        // const resetButton = document.getElementById('reset-matches');
        // resetButton.addEventListener('click', () => this.resetMatches());
    }

    handleResetMatches() {
        const leftContainer = document.querySelector('.match-left');
        document.querySelectorAll('.match-item').forEach(item => {
            leftContainer.appendChild(item);
        });
    }

    handleDragStart(e) {
        this.draggedItem = e.target;
        e.target.classList.add('dragging');
        e.dataTransfer.setData('text/plain', e.target.dataset.itemId);
    }

    handleDragEnd(e) {
        e.target.classList.remove('dragging');
        this.draggedItem = null;
    }

    handleDragOver(e) {
        e.preventDefault();
        e.currentTarget.classList.add('dragover');
    }

    handleDragLeave(e) {
        e.currentTarget.classList.remove('dragover');
    }

    handleDrop(e) {
        e.preventDefault();
        const dropzone = e.currentTarget;
        dropzone.classList.remove('dragover');

        // Return if dropzone already has a matched item
        if (dropzone.querySelector('.match-item')) {
            return;
        }

        const itemId = e.dataTransfer.getData('text/plain');
        const draggedItem = this.draggedItem;

        if (draggedItem) {
            dropzone.insertBefore(draggedItem, dropzone.firstChild);
        }
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

class GridHandler {
    constructor() {
        // super();

        this.selectedCell = null;
        this.gridModal = null;
        this.allDataModal = null;
        // this.eventListenersAttached = false; // Flag to track if event listeners are attached

        // if (document.querySelector('.grid-cell')) {
        this.showPopup = this.showPopup.bind(this);
        this.handleSelectOption = this.handleSelectOption.bind(this);
        this.handleShowAllData = this.handleShowAllData.bind(this);
        this.handleSaveSelections = this.handleSaveSelections.bind(this);
        this.toggleCell = this.toggleCell.bind(this);
        this.selectCell = this.selectCell.bind(this);
        this.updateCellNumbers = this.updateCellNumbers.bind(this);

        this.init();
        // }
    }

    init() {
        if (document.querySelector('.grid-cell')) {
            const gridModalElement = document.getElementById('gridModal');
            const allDataModalElement = document.getElementById('allDataModal');

            if (gridModalElement) {
                this.gridModal = new bootstrap.Modal(gridModalElement);
            }
            
            if (allDataModalElement) {
                this.allDataModal = new bootstrap.Modal(allDataModalElement);
            }
            // this.gridModal = new bootstrap.Modal(document.getElementById('gridModal'));
            // this.allDataModal = new bootstrap.Modal(document.getElementById('allDataModal'));
            this.initGridEvents();
            this.updateCellNumbers();
        }
    }

    cleanup() {
        let elem = document.querySelector('#question-wrapper');
        elem.replaceWith(elem.cloneNode(true));

        // Remove event listeners
        // document.querySelectorAll('.grid-cell').forEach(cell => {
        //     cell.removeEventListener('click', this.boundShowPopup);
        // });

        // document.getElementById('selectOption')?.removeEventListener('click', this.boundSelectOption);
        // document.getElementById('showAllData')?.removeEventListener('click', this.boundShowAllData);
        // document.getElementById('saveSelections')?.removeEventListener('click', this.boundSaveSelections);

        this.selectedCell = null;
        this.gridModal = null;
        this.allDataModal = null;
    }

    reinit() {
        this.init();
        this.restoreSelections();
    }

    restoreSelections() {
        document.querySelectorAll('.grid-cell').forEach(cell => {
            if (cell.classList.contains('selected')) {
                // Restore cell state
                this.selectedCell = cell;
            }
        });
    }

    initGridEvents() {
        document.querySelectorAll('.grid-cell').forEach(cell => {
            cell.addEventListener('click', () => this.showPopup(cell));
        });

        const selectButton = document.getElementById('selectOption');
        if (selectButton) {
            selectButton.addEventListener('click', this.handleSelectOption);
        }

        const showAllButton = document.getElementById('showAllData');
        if (showAllButton) {
            showAllButton.addEventListener('click', this.handleShowAllData);
        }

        const saveButton = document.getElementById('saveSelections');
        if (saveButton) {
            saveButton.addEventListener('click', this.handleSaveSelections);
        }

        // document.getElementById('selectOption').addEventListener('click', this.handleSelectOption);
        // document.getElementById('showAllData').addEventListener('click', this.handleShowAllData);
        // document.getElementById('saveSelections').addEventListener('click', this.handleSaveSelections);
        
        // document.getElementById('selectOption').addEventListener('click', this.boundSelectOption);
        // document.getElementById('showAllData').addEventListener('click', this.boundShowAllData);
        // document.getElementById('saveSelections').addEventListener('click', this.boundSaveSelections);
    }

    handleSelectOption() {
        if (this.selectedCell) {
            this.toggleCell(this.selectedCell);
            // Update the button text after toggling the selection
            const selectButton = document.getElementById('selectOption');
            if (this.selectedCell.classList.contains('selected')) {
                selectButton.textContent = 'Unselect';
            } else {
                selectButton.textContent = 'Select';
            }
        }
        // Safely hide modal
        if (this.gridModal) {
            this.gridModal.hide();
        }
    }

    handleShowAllData() {
        const allCells = document.querySelectorAll('.grid-cell');
        const content = document.getElementById('allDataContent');
        content.innerHTML = '';

        allCells.forEach((cell, index) => {
            const button = cell.querySelector('button');
            if (button) {
                const cellId = button.dataset.cellId;
                const contentType = button.dataset.contentType;
                let cellContent = '';

                if (contentType === 'text') {
                    cellContent = button.dataset.text;
                } else if (contentType === 'image') {
                    cellContent = `<img src="${button.dataset.image}" alt="Option" style="max-width: 100%">`;
                }

                const isChecked = cell.classList.contains('selected') ? 'checked' : '';

                content.innerHTML += `<div class="form-check">
                    <input class="form-check-input" type="checkbox" value="${cellId}" id="checkbox-${cellId}" ${isChecked}>
                    <label class="form-check-label" for="checkbox-${cellId}">
                        <p>No: ${index + 1}</p>
                        <p>Content: ${cellContent}</p>
                    </label>
                </div>`;
            }
        });
        
        this.allDataModal.show();
    }

    handleSaveSelections() {
        const checkboxes = document.querySelectorAll('#allDataContent .form-check-input');
        checkboxes.forEach(checkbox => {
            const cellId = checkbox.value;
            const cell = document.querySelector(`.grid-cell button[data-cell-id="${cellId}"]`).closest('.grid-cell');
            if (checkbox.checked) {
                if (!cell.classList.contains('selected')) {
                    this.selectCell(cell);
                }
            } else {
                if (cell.classList.contains('selected')) {
                    this.toggleCell(cell);
                }
            }
        });
        this.allDataModal.hide();
    }

    showPopup(cell) {
        // const cell = event.currentTarget;
        const content = document.getElementById('popupContent');
        const selectButton = document.getElementById('selectOption');
        this.selectedCell = cell;

        // Assuming the button is a direct child of the cell
        const button = cell.querySelector('button');
        if (button && button.dataset.contentType === 'text') {
            content.innerHTML = button.dataset.text;
        } else {
            content.innerHTML = `<img src="${button.dataset.image}" alt="Option" style="max-width: 100%">`;
        }

        // Set the button text based on the cell's current state
        if (cell.classList.contains('selected')) {
            selectButton.textContent = 'Unselect';
        } else {
            selectButton.textContent = 'Select';
        }

        this.gridModal.show();
    }

    selectCell(cell) {
        // document.querySelectorAll('.grid-cell').forEach(c => c.classList.remove('selected'));
        cell.classList.add('selected');
    }

    toggleCell(cell) {
        cell.classList.toggle('selected');
    }

    updateCellNumbers() {
        const allCells = document.querySelectorAll('.grid-cell');
        allCells.forEach((cell, index) => {
            const button = cell.querySelector('button');
            if (button) {
                const cellNumber = cell.querySelector('.cell-number');
                if (cellNumber) {
                    cellNumber.textContent = `${index + 1}`;
                }
            }
        });
    }

    collectAnswer() {
        const selectedCells = document.querySelectorAll('.grid-cell.selected');
        const answers = Array.from(selectedCells).map(cell => {
            const button = cell.querySelector('button');
            return button ? button.dataset.cellId : null;
        }).filter(answer => answer !== null);

        return answers.length > 0 ? { selected_cells: answers } : null;
    }

    isAnswered() {
        return !!document.querySelector('.grid-cell.selected');
    }
}

class FlashHandler extends MCQHandler {
    constructor() {
        super();
        this.items = [];
        this.currentIndex = 0;
        this.interval = null;
        this.init();
    }

    init() {
        const container = document.querySelector('.flash-question-container');
        if (!container) return;

        // Parse presentation items from data attribute and verify
        const itemsData = container.dataset.items;
        if (!itemsData) return;
        
        this.items = JSON.parse(itemsData);
        if (!this.items || !this.items.length) return;
        
        // Parse presentation items from data attribute
        // this.items = JSON.parse(container.dataset.items);
        this.flashInterval = parseInt(container.dataset.interval) * 1000; // Convert to milliseconds
        this.flashContent = container.querySelector('.flash-content');
        this.flashCounter = container.querySelector('.flash-counter');
        this.optionsContainer = container.querySelector('.flash-options');

        // Start flash sequence immediately
        this.startFlashSequence();
    }

    cleanup() {
        if (this.interval) {
            clearInterval(this.interval);
        }
        this.items = [];
        this.currentIndex = 0;
        this.interval = null;
        
        let elem = document.querySelector('#question-wrapper');
        elem.replaceWith(elem.cloneNode(true));
    }

    reinit() {
        this.cleanup();
        this.init();
    }

    startFlashSequence() {
        this.showItem(0);
        this.interval = setInterval(() => {
            this.currentIndex++;
            if (this.currentIndex < this.items.length) {
                this.showItem(this.currentIndex);
            } else {
                this.endFlashSequence();
            }
        }, this.flashInterval);
    }

    showItem(index) {
        if (!this.items[index]) return;

        const item = this.items[index];
        this.flashCounter.textContent = `Item ${index + 1} of ${this.items.length}`;
        
        // Handle both text and image items
        if (item.image) {
            this.flashContent.innerHTML = `<img src="${item.image}" alt="Flash item ${index + 1}" class="flash-image img-thumbnail">`;
        } else {
            this.flashContent.innerHTML = `<div class="flash-text jumbotron">${item.text}</div>`;

        }
    }

    endFlashSequence() {
        clearInterval(this.interval);
        this.flashContent.innerHTML = '';
        this.flashCounter.textContent = 'Sequence complete';
        this.optionsContainer.classList.remove('d-none');
    }

    // Inherit MCQHandler's collectAnswer and isAnswered methods
}

class MCQParagraphHandler extends MCQHandler {
    constructor() {
        super();
        this.paragraphRead = false;
        this.timer = null;
        this.initParagraphTimer();
    }

    init() {
        this.initParagraphTimer();
    }

    initParagraphTimer() {
        const container = document.querySelector('.paragraph-container');
        if (!container) return;

        const paragraphContent = container.querySelector('.paragraph-content');
        const questionContent = container.querySelector('.question-content');
        const timeDisplay = container.querySelector('.time-display');
        
        let timeLeft = parseInt(container.dataset.interval);
        if (isNaN(timeLeft)) return;

        timeDisplay.textContent = `Time remaining: ${timeLeft} seconds`;

        this.timer = setInterval(() => {
            timeLeft--;
            timeDisplay.textContent = `Time remaining: ${timeLeft} seconds`;
            
            if (timeLeft <= 0) {
                clearInterval(this.timer);
                paragraphContent.classList.add('d-none');
                questionContent.classList.remove('d-none');
                this.paragraphRead = true;
            }
        }, 1000);
    }

    cleanup() {
        if (this.timer) {
            clearInterval(this.timer);
        }
        super.cleanup();
    }

    isAnswered() {
        return super.isAnswered() && this.paragraphRead;
    }

    collectAnswer() {
        const selectedOption = document.querySelector('input[name="answer"]:checked');
        return {
            selected_option: selectedOption ? selectedOption.value : null
        };
    }
}


class QuestionTypeHandler {
    static handlerClasses = {
        mcq_text: MCQHandler,
        mcq_image: MCQHandler,
        mcq_mixed: MCQMixedHandler,
        mcq_audio: AudioHandler,
        mcq_video: VideoHandler,
        mcq_flash: FlashHandler,
        mcq_paragraph: MCQParagraphHandler,
        fib_text: FIBHandler,
        fib_image: FIBHandler,
        fib_audio: FIBAudioHandler,
        fib_video: FIBVideoHandler,
        fib_paragraph: FIBParagraphHandler,
        fib_flash: FIBFlashHandler,
        psy_rating: PsyRatingHandler,
        psy_ranking: RankingHandler,
        cus_hotspot_single: HotspotHandler,
        cus_hotspot_multiple: HotspotHandler,
        cus_match: MatchHandler,
        cus_grid: GridHandler,
    };

    static getHandler(questionType) {
        const HandlerClass = this.handlerClasses[questionType] || BaseHandler;
        return new HandlerClass();
    }
}


class AssessmentManager {
    constructor() {
        this.sessionId = document.getElementById('assessment-timer').dataset.session;
        this.currentQuestionId = null;
        this.isSubmitting = false;
        this.questionTypeHandler = QuestionTypeHandler;
        this.handler = null;
        this.questionHandlers = new Map(); // Track handlers by questionId

        // this.initTimer();
        this.initEventListeners();
        this.loadCurrentQuestion();
        this.startTimer();
    }

    cleanupHandler() {
        // Clean up previous handler if exists
        if (this.handler) {
            this.handler.cleanup?.();
        }
    }

    initCurrentQuestionHandler() {
        const questionWrapper = document.querySelector('#question-wrapper');
        if (questionWrapper) {
            const questionType = questionWrapper.dataset.questionType;
            const currentQuestionId = questionWrapper.dataset.questionId;

            // Check if we have a handler for this specific question
            if (this.questionHandlers.has(currentQuestionId)) {
                this.handler = this.questionHandlers.get(currentQuestionId);
                this.handler.reinit?.();
            } else {
                // Create new handler for this question
                this.handler = this.questionTypeHandler.getHandler(questionType);
                this.questionHandlers.set(currentQuestionId, this.handler);
            }
        } else {
            this.handler = null;
        }
    }

    startTimer() {
        const timerElement = document.getElementById('assessment-timer');
        const duration = parseInt(timerElement.dataset.duration, 10);
        let remainingTime = duration;

        const updateTimer = () => {
            const minutes = Math.floor(remainingTime / 60);
            const seconds = remainingTime % 60;
            timerElement.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;
            if (remainingTime > 0) {
                remainingTime -= 1;
                setTimeout(updateTimer, 1000);
            } else {
                this.submitAssessment();
            }
        };

        updateTimer();
    }

    updateTimer(startTime, duration) {
        const now = new Date();
        const elapsed = Math.floor((now - startTime) / 1000);
        const remaining = duration - elapsed;

        if (remaining <= 0) {
            clearInterval(this.timerInterval);
            this.submitAssessment(true);
            return;
        }

        const hours = Math.floor(remaining / 3600);
        const minutes = Math.floor((remaining % 3600) / 60);
        const seconds = remaining % 60;
        
        document.getElementById('time-display').textContent = 
            `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    }

    initEventListeners() {
        // Navigation events
        document.querySelectorAll('.question-item').forEach(item => {
            item.addEventListener('click', () => this.loadQuestion(item.dataset.questionId));
        });

        document.getElementById('prev-question').addEventListener('click', () => this.navigateQuestion('prev'));
        document.getElementById('next-question').addEventListener('click', () => this.navigateQuestion('next'));
        
        document.getElementById('bookmark-question').addEventListener('click', () => this.toggleBookmark());
        document.getElementById('suspend-assessment').addEventListener('click', () => this.suspendAssessment());
        document.getElementById('submit-assessment').addEventListener('click', () => this.submitAssessment());

        // Auto-save on input changes
        // document.getElementById('question-content').addEventListener('change', (e) => {
        //     if (e.target.matches('input, select, textarea')) {
        //         this.saveCurrentAnswer();
        //     }
        // });


    }

    loadCurrentQuestion() {
        const questionContent = document.querySelector('#question-wrapper');
        if (questionContent && questionContent.dataset.questionId) {
            this.currentQuestionId = questionContent.dataset.questionId;

            // Initialize handler for initial server-side rendered question
            this.initCurrentQuestionHandler();

            this.updateNavigationState();
            // this.highlightCurrentQuestion(this.currentQuestionId);
        } else {
            const firstQuestionItem = document.querySelector('.question-item');
            if (firstQuestionItem) {
                const questionId = firstQuestionItem.dataset.questionId;
                this.loadQuestion(questionId);
            }
        }
    }

    async loadQuestion(questionId) {
        try {
            this.cleanupHandler();

            const response = await fetch(`/assessment/api/session/${this.sessionId}/question/${questionId}/`);
            const html = await response.text();
            document.getElementById('question-content').innerHTML = html;
            this.currentQuestionId = questionId;

            this.initCurrentQuestionHandler();
            this.updateNavigationState();
        } catch (error) {
            console.error('Error loading question:', error);
        }
    }

    // navigateQuestion(direction) {
    //     const currentItem = document.querySelector(`.question-item[data-question-id="${this.currentQuestionId}"]`);
    //     let nextItem;

    //     if (direction === 'next') {
    //         nextItem = currentItem.nextElementSibling;
    //     } else if (direction === 'prev') {
    //         nextItem = currentItem.previousElementSibling;
    //     }

    //     if (nextItem) {
    //         this.loadQuestion(nextItem.dataset.questionId);
    //     }
    // }

    async navigateQuestion(direction) {
        const currentItem = document.querySelector(`.question-item[data-question-id="${this.currentQuestionId}"]`);
        let nextItem;
    
        // Get the current question type and handler
        //const questionType = document.querySelector('#question-wrapper').dataset.questionType;
        //const handler = this.questionTypeHandler.getHandler(questionType);
    
        // Check if current question is answered using the handler's isAnswered method
        const isCurrentQuestionAnswered = this.handler.isAnswered();
    
        if (!isCurrentQuestionAnswered) {
            // Show warning modal/alert
            if (!confirm('Current question is not answered. Do you want to proceed?')) {
                return;
            }
        } else {
            // Save the answer before navigation
            await this.saveCurrentAnswer();
        }
    
        // Proceed with navigation
        if (direction === 'next') {
            nextItem = currentItem.nextElementSibling;
        } else if (direction === 'prev') {
            nextItem = currentItem.previousElementSibling;
        }
    
        if (nextItem) {
            this.loadQuestion(nextItem.dataset.questionId);
        }
    }    

    updateNavigationState() {
        // Update active question indicator
        document.querySelectorAll('.question-item').forEach(item => {
            if (item.dataset.questionId === this.currentQuestionId) {
                item.classList.add('active');
            } else {
                item.classList.remove('active');
            }
        });

        // Update navigation buttons state
        const currentItem = document.querySelector(`.question-item[data-question-id="${this.currentQuestionId}"]`);
        const prevButton = document.getElementById('prev-question');
        const nextButton = document.getElementById('next-question');

        if (prevButton) {
            prevButton.disabled = !currentItem.previousElementSibling;
        }
        if (nextButton) {
            nextButton.disabled = !currentItem.nextElementSibling;
        }
    }

    updateQuestionStatus(questionId, isAnswered) {
        const questionItem = document.querySelector(`.question-item[data-question-id="${questionId}"]`);
        if (questionItem) {
            if (isAnswered) {
                questionItem.classList.add('answered');
            } else {
                questionItem.classList.remove('answered');
            }
            this.updateSectionProgress(questionItem.dataset.sectionId);
        }
    }

    updateSectionProgress(sectionId) {
        const section = document.querySelector(`.section-block[data-section-id="${sectionId}"]`);
        if (section) {
            const total = section.querySelectorAll('.question-item').length;
            const answered = section.querySelectorAll('.question-item.answered').length;
            const progress = (answered / total * 100).toFixed(1);
            
            section.querySelector('.progress-bar').style.width = `${progress}%`;
            section.querySelector('.progress-bar').textContent = `${progress}%`;
        }
    }

    async saveCurrentAnswer() {
        if (!this.currentQuestionId) return;
        
        //const questionType = document.querySelector('#question-wrapper').dataset.questionType;
        //const handler = this.questionTypeHandler.getHandler(questionType);
        const answerData = this.handler.collectAnswer();

        //const answerData = this.collectAnswerData();
        try {
            await fetch(`/assessment/api/session/${this.sessionId}/save-answer/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                },
                body: JSON.stringify({
                    question_id: this.currentQuestionId,
                    answer_data: answerData
                })
            });
            this.updateQuestionStatus(this.currentQuestionId, true);
        } catch (error) {
            console.error('Error saving answer:', error);
        }
    }

    collectAnswerData() {
        const questionContent = document.getElementById('question-wrapper');
        const questionType = questionContent.dataset.questionType;

        switch (questionType) {
            case 'mcq_text':
            case 'mcq_image':
            case 'mcq_mixed':
            case 'mcq_audio':
            case 'mcq_video':
            case 'mcq_paragraph':
                return {
                    selected_option: document.querySelector('input[name="answer"]:checked')?.value
                };
            case 'fib_text':
                return {
                    answers: Array.from(document.querySelectorAll('.fib-input')).map(input => input.value)
                };
            // Add other question types handling here
            default:
                return {};
        }
    }

    async suspendAssessment() {
        try {
            const response = await fetch(`/assessment/api/session/${this.sessionId}/control/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                },
                body: JSON.stringify({ action: 'suspend' })
            });
            const data = await response.json();
            if (data.status === 'success') {
                window.location.href = '/assessment/suspended/';
            }
        } catch (error) {
            console.error('Error suspending assessment:', error);
        }
    }

    async toggleBookmark() {
        if (!this.currentQuestionId) return;

        try {
            const response = await fetch(`/assessment/api/session/${this.sessionId}/bookmark/${this.currentQuestionId}/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                }
            });
            
            const data = await response.json();
            const bookmarkButton = document.getElementById('bookmark-question');
            
            if (data.bookmarked) {
                bookmarkButton.classList.add('bookmarked');
            } else {
                bookmarkButton.classList.remove('bookmarked');
            }
        } catch (error) {
            console.error('Error toggling bookmark:', error);
        }
    }

    async confirmSubmission() {
        // Check for any unanswered questions
        const unansweredQuestions = Array.from(document.querySelectorAll('.question-item')).filter(item => {
            return !item.classList.contains('answered');
        });
    
        if (unansweredQuestions.length > 0) {
            return confirm(`You have ${unansweredQuestions.length} unanswered questions. Are you sure you want to submit?`);
        }
    
        return confirm('Are you sure you want to submit your assessment?');
    }    

    async submitAssessment(isTimeout = false) {
        if (this.isSubmitting) return;
        this.isSubmitting = true;

        // Save the final question's answer before submission
        await this.saveCurrentAnswer();

        if (!isTimeout) {
            const confirmed = await this.confirmSubmission();
            if (!confirmed) {
                this.isSubmitting = false;
                return;
            }
        }

        try {
            const response = await fetch(`/assessment/api/session/${this.sessionId}/control/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                },
                body: JSON.stringify({ action: 'submit' })
            });
            const data = await response.json();
            if (data.status === 'success') {
                window.location.href = data.redirect_url;
            }
        } catch (error) {
            console.error('Error submitting assessment:', error);
            this.isSubmitting = false;
        }
    }

    getCsrfToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]').value;
    }
}

// Initialize assessment when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new AssessmentManager();
});
