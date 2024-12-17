class TimedQuestionDisplay {
    constructor() {
        this.currentTimer = null;
        this.flashIndex = 0;
    }

    displayQuestion(questionData) {
        const questionContainer = document.getElementById('question-content');
        
        switch(questionData.display_type) {
            case 'paragraph_timed':
                this.handleParagraphDisplay(questionData, questionContainer);
                break;
            case 'flash_words':
            case 'flash_images':
                this.handleFlashDisplay(questionData, questionContainer);
                break;
            case 'image_timed':
                this.handleImageDisplay(questionData, questionContainer);
                break;
        }
    }

    handleParagraphDisplay(questionData, container) {
        // Show paragraph
        container.innerHTML = `
            <div class="timed-paragraph">
                <div class="timer-display"></div>
                <div class="content">${questionData.title}</div>
            </div>
        `;
        
        this.startTimer(questionData.display_time, () => {
            container.innerHTML = this.getQuestionOptions(questionData);
        });
    }

    handleFlashDisplay(questionData, container) {
        const flashItems = questionData.options;
        this.flashIndex = 0;
        
        const showNextFlash = () => {
            if (this.flashIndex < flashItems.length) {
                container.innerHTML = `
                    <div class="flash-item">
                        <div class="timer-display"></div>
                        <div class="content">${flashItems[this.flashIndex].text}</div>
                    </div>
                `;
                this.flashIndex++;
                
                this.startTimer(questionData.display_time, showNextFlash);
            } else {
                container.innerHTML = this.getQuestionOptions(questionData);
            }
        };
        
        showNextFlash();
    }

    handleImageDisplay(questionData, container) {
        container.innerHTML = `
            <div class="timed-image">
                <div class="timer-display"></div>
                <img src="${questionData.image_url}" alt="Question Image">
            </div>
        `;
        
        this.startTimer(questionData.display_time, () => {
            container.innerHTML = this.getQuestionOptions(questionData);
        });
    }

    startTimer(duration, callback) {
        clearTimeout(this.currentTimer);
        
        const timerDisplay = document.querySelector('.timer-display');
        let timeLeft = duration;
        
        const updateTimer = () => {
            timerDisplay.textContent = `Time remaining: ${timeLeft}s`;
            timeLeft--;
            
            if (timeLeft >= 0) {
                setTimeout(updateTimer, 1000);
            } else {
                callback();
            }
        };
        
        updateTimer();
    }

    getQuestionOptions(questionData) {
        // Return HTML for question options based on question type
        let optionsHtml = '<div class="question-options">';
        questionData.options.forEach(option => {
            optionsHtml += `
                <div class="option">
                    <input type="radio" name="answer" value="${option.id}">
                    <label>${option.text}</label>
                </div>
            `;
        });
        optionsHtml += '</div>';
        return optionsHtml;
    }
}