class QuestionTypeHandler {
    constructor() {
        this.timerHandler = new TimerHandler();
    }

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
                                <img src="${opt.image_url}" alt="${opt.text}">
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
                                ${opt.image_url ? `<img src="${opt.image_url}">` : ''}
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
        return this.timerHandler.handleTimedContent(`
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
                    <img src="${question.image_url}" alt="Hotspot Image">
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
                    <img src="${question.image_url}" alt="Hotspot Image">
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

    renderFIBImage(question) {
        return `
            <div class="question-content fib-image">
                <img src="${question.image_url}" alt="Question Image">
                <div class="fib-inputs">
                    ${question.blanks.map(blank => `
                        <input type="text" class="fib-input" data-id="${blank.id}">
                    `).join('')}
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
            <div class="question-content psy-rating">
                <div class="question-text">${question.title}</div>
                <div class="rating-scale">
                    ${question.items.map(item => `
                        <div class="rate-item">
                            <span>${item.text}</span>
                            <div class="scale">
                                ${Array(question.scale_points).fill().map((_, i) => `
                                    <input type="radio" name="rate_${item.id}" value="${i + 1}">
                                `).join('')}
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }
}

class TimerHandler {
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
                this.showQuestionOptions();
            }
        }, 1000);
        
        return container.outerHTML;
    }

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

    showQuestionOptions() {
        const optionsContainer = document.createElement('div');
        optionsContainer.className = 'question-options';
        // Render question options after timed content
        document.querySelector('.content-area').appendChild(optionsContainer);
    }
}


// Initialize and export
const questionHandler = new QuestionTypeHandler();
export default questionHandler;
