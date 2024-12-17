class QuestionManager {
    constructor() {
        this.currentTimer = null;
        this.flashIndex = 0;
        this.sessionId = null;
        this.currentQuestionIndex = 0;
        this.questions = [];
        this.assessment = null;
    }

    initialize(sessionId, assessmentData, ) {
        this.sessionId = sessionId;
        this.assessment = assessmentData;
        this.questions = this.flattenQuestions(assessmentData.sections);
        this.setupEventListeners();
        this.loadQuestion(0);
        this.startAssessmentTimer(this.assessment.duration_minutes * 60);

        // this.sessionId = sessionId;
        // this.assessment = assessmentData;
        // this.questions = this.flattenQuestions(assessmentData);
        // this.setupEventListeners();
        // this.loadQuestion(0);
        // this.startAssessmentTimer(assessmentData.time_remaining);
    }

    flattenQuestions(sections) {
        let questions = [];
        sections.forEach(section => {
            questions = questions.concat(this.getQuestionsFromSection(section));
        });
        return questions;
        // let questions = [];
        // structure.forEach(section => {
        //     if (section.questions) {
        //         questions = questions.concat(section.questions);
        //     }
        // });
        // return this.assessment.display_order === 'random' ? this.shuffleQuestions(questions) : questions;
    }

    getQuestionsFromSection(section) {
        let questions = [...section.questions];
        section.children.forEach(child => {
            questions = questions.concat(this.getQuestionsFromSection(child));
        });
        return questions;
    }

    shuffleQuestions(questions) {
        for (let i = questions.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [questions[i], questions[j]] = [questions[j], questions[i]];
        }
        return questions;
    }

    setupEventListeners() {
        document.getElementById('prev-btn').addEventListener('click', () => this.navigateQuestion('prev'));
        document.getElementById('next-btn').addEventListener('click', () => this.navigateQuestion('next'));
        document.getElementById('submit-btn').addEventListener('click', () => this.submitAssessment());
    }

    startAssessmentTimer(timeRemaining) {
        const timerDisplay = document.getElementById('assessment-timer');
        let timeLeft = timeRemaining;

        const updateTimer = () => {
            const minutes = Math.floor(timeLeft / 60);
            const seconds = timeLeft % 60;
            timerDisplay.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;
            
            if (timeLeft <= 0) {
                this.submitAssessment();
            } else {
                timeLeft--;
                setTimeout(updateTimer, 1000);
            }
        };

        updateTimer();
    }

    navigateQuestion(direction) {
        this.saveCurrentAnswer();
        if (direction === 'prev' && this.currentQuestionIndex > 0) {
            this.currentQuestionIndex--;
        } else if (direction === 'next' && this.currentQuestionIndex < this.questions.length - 1) {
            this.currentQuestionIndex++;
        }
        this.loadQuestion(this.currentQuestionIndex);
        this.updateNavigation();
    }


    updateNavigation() {
        const prevBtn = document.getElementById('prev-btn');
        const nextBtn = document.getElementById('next-btn');
        const submitBtn = document.getElementById('submit-btn');

        prevBtn.disabled = this.currentQuestionIndex === 0;
        nextBtn.style.display = this.currentQuestionIndex === this.questions.length - 1 ? 'none' : 'block';
        submitBtn.style.display = this.currentQuestionIndex === this.questions.length - 1 ? 'block' : 'none';
    }

    highlightCurrentQuestion(questionId) {
        document.querySelectorAll('.question-item').forEach(item => {
            item.classList.remove('active');
        });
        document.querySelector(`.question-item[data-question-id="${questionId}"]`)?.classList.add('active');
    }

    showQuestionOptions(questionData) {
        const optionsContainer = document.createElement('div');
        optionsContainer.className = 'question-options';
        
        switch(questionData.type) {
            case 'mcq_text':
            case 'mcq_image':
            case 'mcq_mixed':
            case 'mcq_audio':
            case 'mcq_video':
            case 'mcq_paragraph':
                optionsContainer.innerHTML = this.renderMCQOptions(questionData.options);
                break;
            case 'fib_text':
            case 'fib_image':
                optionsContainer.innerHTML = this.renderFIBOptions(questionData.blanks);
                break;
            case 'cus_grid':
                optionsContainer.innerHTML = this.renderGridOptions(questionData.grid_items);
                break;
            case 'cus_match':
                optionsContainer.innerHTML = this.renderMatchOptions(questionData.pairs);
                break;
            case 'psy_ranking':
                optionsContainer.innerHTML = this.renderRankingOptions(questionData.items);
                break;
        }

        document.querySelector('.content-area').appendChild(optionsContainer);
        this.setupOptionInteractions(questionData.type);
    }

    setupOptionInteractions(questionType) {
        switch(questionType) {
            case 'cus_grid':
                this.setupGridSelectionHandlers();
                break;
            case 'cus_match':
                this.setupMatchingDragDrop();
                break;
            case 'psy_ranking':
                this.setupRankingSortable();
                break;
            case 'cus_hotspot_single':
            case 'cus_hotspot_multiple':
                this.setupHotspotHandlers();
                break;
        }
    }
    
    setupGridSelectionHandlers() {
        const gridCells = document.querySelectorAll('.grid-cell');
        gridCells.forEach(cell => {
            cell.addEventListener('click', () => {
                cell.classList.toggle('selected');
            });
        });
    }
    
    setupMatchingDragDrop() {
        const draggables = document.querySelectorAll('.match-item');
        draggables.forEach(item => {
            item.setAttribute('draggable', true);
            item.addEventListener('dragstart', this.handleDragStart);
            item.addEventListener('dragover', this.handleDragOver);
            item.addEventListener('drop', this.handleDrop);
        });
    }
    
    setupRankingSortable() {
        const rankingContainer = document.getElementById('ranking-container');
        const items = rankingContainer.querySelectorAll('.rank-item');
        items.forEach(item => {
            item.setAttribute('draggable', true);
            item.addEventListener('dragstart', this.handleDragStart);
            item.addEventListener('dragover', this.handleDragOver);
            item.addEventListener('drop', this.handleDrop);
        });
    }
    
    setupHotspotHandlers() {
        const hotspots = document.querySelectorAll('.hotspot');
        hotspots.forEach(spot => {
            spot.addEventListener('click', () => {
                if (spot.closest('.hotspot-single')) {
                    hotspots.forEach(s => s.classList.remove('selected'));
                }
                spot.classList.toggle('selected');
            });
        });
    }
    
    collectMatchingPairs() {
        const matches = [];
        const matchedPairs = document.querySelectorAll('.match-pair');
        matchedPairs.forEach(pair => {
            matches.push({
                left_id: pair.querySelector('.left-item').dataset.id,
                right_id: pair.querySelector('.right-item').dataset.id
            });
        });
        return matches;
    }

    collectRankingOrder() {
        return Array.from(document.querySelectorAll('.rank-item'))
            .map(item => item.dataset.id);
    }

    collectRatingValue() {
        const container = document.getElementById('question-container');
        const selectedRating = container.querySelector('input[name="rating"]:checked');
        
        return {
            rating_value: selectedRating ? selectedRating.value : null,
            rating_id: selectedRating ? selectedRating.id.replace('rating_', '') : null
        };
    }

    handleDragStart(e) {
        e.dataTransfer.setData('text/plain', e.target.dataset.id);
        e.target.classList.add('dragging');
    }

    handleDragOver(e) {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'move';
    }

    handleDrop(e) {
        e.preventDefault();
        const draggedId = e.dataTransfer.getData('text/plain');
        const draggedElement = document.querySelector(`[data-id="${draggedId}"]`);
        const dropTarget = e.target.closest('.rank-item') || e.target.closest('.match-item');
        
        if (dropTarget && draggedElement !== dropTarget) {
            const tempHtml = dropTarget.innerHTML;
            const tempId = dropTarget.dataset.id;
            
            dropTarget.innerHTML = draggedElement.innerHTML;
            dropTarget.dataset.id = draggedElement.dataset.id;
            
            draggedElement.innerHTML = tempHtml;
            draggedElement.dataset.id = tempId;
        }
        
        document.querySelector('.dragging')?.classList.remove('dragging');
    }

    renderMCQOptions(options) {
        return `
            <div class="mcq-options">
                ${options.map(opt => `
                    <div class="option">
                        <input type="radio" name="answer" value="${opt.id}" id="opt-${opt.id}">
                        <label for="opt-${opt.id}">${opt.text}</label>
                    </div>
                `).join('')}
            </div>
        `;
    }

    renderFIBOptions(blanks) {
        return `
            <div class="fib-options">
                ${blanks.map(blank => `
                    <input type="text" class="fib-input" data-id="${blank.id}" placeholder="${blank.placeholder || 'Enter answer'}">
                `).join('')}
            </div>
        `;
    }

    renderGridOptions(items) {
        return `
            <div class="grid-options">
                ${items.map(item => `
                    <div class="grid-cell" data-id="${item.id}" data-row="${item.row}" data-col="${item.col}">
                        ${item.text}
                    </div>
                `).join('')}
            </div>
        `;
    }

    renderMatchOptions(pairs) {
        return `
            <div class="matching-container">
                <div class="left-items">
                    ${pairs.map(pair => `
                        <div class="match-item left-item" data-id="${pair.id}">${pair.left_text}</div>
                    `).join('')}
                </div>
                <div class="right-items">
                    ${pairs.map(pair => `
                        <div class="match-item right-item" data-id="${pair.id}">${pair.right_text}</div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    renderRankingOptions(items) {
        return `
            <div class="ranking-container" id="ranking-container">
                ${items.map(item => `
                    <div class="rank-item" draggable="true" data-id="${item.id}">
                        ${item.text}
                    </div>
                `).join('')}
            </div>
        `;
    }


    saveCurrentAnswer() {
        const question = this.questions[this.currentQuestionIndex];
        const answerData = this.collectAnswerData(question.type);
        this.saveAnswer(question.question_id, answerData);
    }

    collectAnswerData(questionType) {
        const container = document.getElementById('question-container');
        let answerData = {};

        switch(questionType) {
            case 'mcq_text':
            case 'mcq_image':
            case 'mcq_mixed':
            case 'mcq_audio':
            case 'mcq_video':
            case 'mcq_paragraph':
                answerData.selected_option = container.querySelector('input[name="answer"]:checked')?.value;
                break;
            case 'fib_text':
            case 'fib_image':
                answerData.answers = Array.from(container.querySelectorAll('.fib-input')).map(input => ({
                    blank_id: input.dataset.id,
                    value: input.value
                }));
                break;
            case 'cus_grid':
                answerData.selected_cells = Array.from(container.querySelectorAll('.grid-cell.selected')).map(cell => cell.dataset.id);
                break;
            case 'cus_match':
                answerData.matches = this.collectMatchingPairs();
                break;
            case 'psy_rating':
                answerData.rating = this.collectRatingValue();
                break;
            case 'psy_ranking':
                answerData.ranking = this.collectRankingOrder();
                break;
        }

        return answerData;
    }

    loadQuestion(index) {
        const question = this.questions[index];
        fetch(`/assessment/api/question/${question.question_id}/`)
            .then(response => response.json())
            .then(data => {
                const container = document.getElementById('question-container');
                /*if (data.display_time) {
                    container.innerHTML = this.handleTimedContent(
                        this.renderQuestionByType(data),
                        data.display_time
                    );
                } else if (data.type.includes('flash')) {
                    container.innerHTML = this.handleFlashContent(
                        data.flash_items,
                        data.flash_time
                    );
                } else {*/
                    container.innerHTML = this.renderQuestionByType(data);
                //}
                this.highlightCurrentQuestion(question.question_id);
                this.setupOptionInteractions(data.type);
            });
    }

    // ... [Previous timer and flash content handlers] ...
    handleTimedContent(content, displayTime) {
        const container = document.createElement('div');
        container.className = 'timed-content-container';
        
        // Initial display with timer
        container.innerHTML = `
            <div class="timer-bar">
                <div class="timer-progress"></div>
                <span class="timer-text">${displayTime}</span>
            </div>
            <div class="content-area">
                ${content}
            </div>
        `;
        
        // Start timer animation
        const progressBar = container.querySelector('.timer-progress');
        const timerText = container.querySelector('.timer-text');
        progressBar.style.transition = `width ${displayTime}s linear`;
        progressBar.style.width = '0%';
        
        let timeLeft = displayTime;
        const timer = setInterval(() => {
            timeLeft--;
            timerText.textContent = timeLeft;
            
            if (timeLeft <= 0) {
                clearInterval(timer);
                container.querySelector('.content-area').style.display = 'none';
                container.querySelector('.timer-bar').style.display = 'none';
                //this.showQuestionOptions(question.type);
            }
        }, 1000);
        
        return container.outerHTML;
    }
    
    /*handleTimedContent(content, displayTime) {
        const container = document.getElementById('question-container');
        container.innerHTML = content; //`
        //    <div class="timed-content">
        //        <div class="timer">Time remaining: <span id="display-timer">${displayTime}</span>s</div>
        //        <div class="content">${content}</div>
        //    </div>
        //`;

        let timeLeft = displayTime;  // Already in seconds
        const timerInterval = setInterval(() => {
            timeLeft--;
            const timerDisplay = document.getElementById('display-timer');
            if (timerDisplay) {
                timerDisplay.textContent = timeLeft;
            }
            
            if (timeLeft <= 0) {
                clearInterval(timerInterval);
                //container.innerHTML = content;
                container.innerHTML = `
                    <div class="alert alert-info">
                        Time's up! The paragraph content is no longer available.
                    </div>
                `;
            }
        }, 1000);  // Update every second
    }*/


    handleFlashContent(items, flashTime) {
        const container = document.createElement('div');
        container.className = 'flash-content-container';
        
        let currentIndex = 0;
        const totalItems = items.length;
        
        // Setup flash display structure
        container.innerHTML = `
            <div class="flash-display">
                <div class="flash-progress">
                    <span class="current-index">1</span>/${totalItems}
                </div>
                <div class="flash-item"></div>
                <div class="flash-timer"></div>
            </div>
        `;
        
        const flashItem = container.querySelector('.flash-item');
        const progressText = container.querySelector('.current-index');
        const timerDisplay = container.querySelector('.flash-timer');
        
        const showNextItem = () => {
            if (currentIndex < totalItems) {
                flashItem.innerHTML = items[currentIndex].content;
                progressText.textContent = currentIndex + 1;
                
                let itemTimeLeft = flashTime;
                timerDisplay.textContent = itemTimeLeft;
                
                const itemTimer = setInterval(() => {
                    itemTimeLeft--;
                    timerDisplay.textContent = itemTimeLeft;
                    
                    if (itemTimeLeft <= 0) {
                        clearInterval(itemTimer);
                        currentIndex++;
                        if (currentIndex < totalItems) {
                            showNextItem();
                        } else {
                            this.showQuestionOptions();
                        }
                    }
                }, 1000);
            }
        };
        
        showNextItem();
        return container.outerHTML;
    }


    renderQuestionByType(question) {
        const renderMethods = {
            'mcq_text': this.renderMCQText,
            'mcq_image': this.renderMCQImage,
            'mcq_mixed': this.renderMCQMixed,
            'mcq_audio': this.renderMCQAudio,
            'mcq_video': this.renderMCQVideo,
            'mcq_paragraph': this.renderMCQParagraph,
            'mcq_flash': this.renderMCQFlash,
            'cus_hotspot_single': this.renderHotspotSingle,
            'cus_hotspot_multiple': this.renderHotspotMultiple,
            'fib_text': this.renderFIBText,
            'fib_image': this.renderFIBImage,
            'fib_audio': this.renderFIBAudio,
            'fib_video': this.renderFIBVideo,
            'fib_paragraph': this.renderFIBParagraph,
            'fib_flash': this.renderFIBFlash,
            'cus_grid': this.renderGridList,
            'cus_match': this.renderMatchFollowing,
            'psy_ranking': this.renderPsyRanking,
            'psy_rank_n_rate': this.renderPsyRankRate,
            'psy_rating': this.renderPsyRating,
            'psy_forced_single': this.renderPsyForcedSingle,
            'psy_forced_two': this.renderPsyForcedTwo
        };

        return renderMethods[question.type]?.call(this, question) || 
               `<div class="error">Unknown question type: ${question.type}</div>`;
    }

    // ... [All individual render methods for each question type] ...
    renderMCQText(question) {
        return `
            <div class="question-content mcq-text">
                <div class="question-text">${question.title}</div>
                <div class="options">
                    ${question.options.map(opt => `
                        <div class="option">
                            <input type="radio" name="answer" value="${opt.id}" id="opt-${opt.id}">
                            <label for="opt-${opt.id}">${opt.text}</label>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    renderMCQImage(question) {
        return `
            <div class="question-content mcq-image">
                <div class="question-text">${question.title}</div>
                <div class="image-options">
                    ${question.options.map(opt => `
                        <div class="image-option">
                            <input type="radio" name="answer" value="${opt.id}" id="opt-${opt.id}">
                            <label for="opt-${opt.id}">
                                <img src="${opt.image_url}" alt="${opt.text}" class="img-fluid rounded">
                            </label>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    renderMCQMixed(question) {
        return `
            <div class="question-content mcq-mixed">
                <div class="question-text">${question.title}</div>
                <div class="mixed-content">${question.content}</div>
                <div class="mixed-options">
                    ${question.options.map(opt => `
                        <div class="mixed-option">
                            <input type="radio" name="answer" value="${opt.id}" id="opt-${opt.id}">
                            <label for="opt-${opt.id}">
                                ${opt.image_url ? `<img src="${opt.image_url}" class="img-fluid rounded">` : ''}
                                <span>${opt.text}</span>
                            </label>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    renderMCQAudio(question) {
        return `
            <div class="question-content mcq-audio">
                <div class="question-text">${question.title}</div>
                <audio controls src="${question.audio_url}"></audio>
                <div class="audio-options">
                    ${question.options.map(opt => `
                        <div class="option">
                            <input type="radio" name="answer" value="${opt.id}" id="opt-${opt.id}">
                            <label for="opt-${opt.id}">${opt.text}</label>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    renderMCQVideo(question) {
        return `
            <div class="question-content mcq-video">
                <div class="question-text">${question.title}</div>
                <video controls src="${question.video_url}"></video>
                <div class="video-options">
                    ${question.options.map(opt => `
                        <div class="option">
                            <input type="radio" name="answer" value="${opt.id}" id="opt-${opt.id}">
                            <label for="opt-${opt.id}">${opt.text}</label>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    renderMCQParagraph(question) {
        return this.handleTimedContent(`
            <div class="question-content mcq-paragraph">
                <div class="paragraph-text">${question.paragraph}</div>
                <div class="question-text">${question.title}</div>
                <div class="options">
                    ${question.options.map(opt => `
                        <div class="option">
                            <input type="radio" name="answer" value="${opt.id}" id="opt-${opt.id}">
                            <label for="opt-${opt.id}">${opt.text}</label>
                        </div>
                    `).join('')}
                </div>
            </div>
        `, question.display_time);
    }

    renderHotspotSingle(question) {
        return `
            <div class="question-content hotspot-single">
                <div class="question-text">${question.title}</div>
                <div class="hotspot-container" id="hotspot-area">
                    <img src="${question.image_url}" alt="Hotspot Image" class="img-fluid rounded">
                    ${question.hotspots.map(spot => `
                        <div class="hotspot" 
                             data-id="${spot.id}"
                             style="left: ${spot.x}%; top: ${spot.y}%">
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    renderHotspotMultiple(question) {
        return `
            <div class="question-content hotspot-multiple">
                <div class="question-text">${question.title}</div>
                <div class="hotspot-container" id="hotspot-area">
                    <img src="${question.image_url}" alt="Hotspot Image" class="img-fluid rounded">
                    ${question.hotspots.map(spot => `
                        <div class="hotspot" 
                             data-id="${spot.id}"
                             style="left: ${spot.x}%; top: ${spot.y}%">
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    renderMCQFlash(question) {
        return this.timerHandler.handleFlashContent(question.flash_items, question.flash_time);
    }

    renderFIBText(question) {
        return `
            <div class="question-content fib-text">
                <div class="question-text">${this.processFIBText(question.text)}</div>
            </div>
        `;
    }

    processFIBText(text) {
        let processedText = text;
        const blanks = text.match(/\{\{.*?\}\}/g) || [];
        
        blanks.forEach((blank, index) => {
            const blankId = blank.replace(/[{}]/g, '');
            processedText = processedText.replace(
                blank,
                `<input type="text" class="fib-input" data-id="${blankId}" placeholder="Enter answer">`
            );
        });
        
        return processedText;
    }
    

    renderFIBImage(question) {
        return `
            <div class="question-content fib-image">
                <img src="${question.image_url}" alt="Question Image" class="img-fluid rounded">
                <div class="fib-inputs">
                    ${question.blanks.map((blank, index) => { return `
                        <input type="text" class="fib-input" data-id="${index}">
                    `}).join('')}
                </div>
            </div>
        `;
    }

    renderGridList(question) {
        return `
            <div class="question-content grid-list">
                <div class="question-text">${question.title}</div>
                <div class="grid-container">
                    ${question.grid_items.map(item => `
                        <div class="grid-item" data-id="${item.id}">
                            ${item.text}
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    renderMatchFollowing(question) {
        return `
            <div class="question-content match-following">
                <div class="question-text">${question.title}</div>
                <div class="match-container">
                    <div class="left-items">
                        ${question.left_items.map(item => `
                            <div class="match-item" data-id="${item.id}">${item.text}</div>
                        `).join('')}
                    </div>
                    <div class="right-items">
                        ${question.right_items.map(item => `
                            <div class="match-item" data-id="${item.id}">${item.text}</div>
                        `).join('')}
                    </div>
                </div>
            </div>
        `;
    }

    renderPsyRanking(question) {
        return `
            <div class="question-content psy-ranking">
                <div class="question-text">${question.title}</div>
                <div class="ranking-items" id="ranking-container">
                    ${question.items.map(item => `
                        <div class="rank-item" draggable="true" data-id="${item.id}">
                            ${item.text}
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    renderPsyRating(question) {
        return `
            <div class="question-content">
                <div class="question-header mb-4">
                    <h4 class="question-title">${question.title}</h4>
                    <div class="question-text mt-3">${question.text}</div>
                </div>
                <div class="rating-items">
                    <div class="btn-group rating-buttons w-100" role="group">
                        ${question.rating_options.map(option => `
                            <input type="radio" 
                                class="btn-check" 
                                name="rating" 
                                id="rating_${option.id}" 
                                value="${option.value}">
                            <label class="btn btn-outline-primary d-flex flex-column" 
                                for="rating_${option.id}">
                                <span class="rating-text">${option.text}</span>
                            </label>
                        `).join('')}
                    </div>
                </div>
            </div>
            
            <!-- Instructions Modal -->
            <div class="modal fade" id="instructionsModal" tabindex="-1">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Instructions</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            ${question.instructions}
                        </div>
                    </div>
                </div>
            </div>
        `;
    }


    saveAnswer(questionId, answerData) {
        return fetch(`/assessment/api/save-answer/${this.sessionId}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            },
            body: JSON.stringify({
                question_id: questionId,
                answer_data: answerData
            })
        });
    }

    submitAssessment() {
        this.saveCurrentAnswer();
        fetch(`/assessment/submit/${this.sessionId}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            }
        }).then(response => {
            if (response.ok) {
                window.location.href = `/assessment/results/${this.sessionId}/`;
            }
        });
    }
}
