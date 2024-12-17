class QuestionManager {
    constructor() {
        this.currentIndex = 0;
        this.questions = [];
        this.assessment = null;
        this.session = null;
    }

    initialize(sessionId, assessmentData) {
        this.sessionId = sessionId;
        this.assessment = assessmentData.assessment;
        this.session = assessmentData.session;
        this.questions = this.flattenQuestions(assessmentData.sections);
        this.setupEventListeners();
        this.loadQuestion(0);
        this.startAssessmentTimer(this.session.time_remaining);
    }

    flattenQuestions(sections) {
        let questions = [];
        sections.forEach(section => {
            questions = questions.concat(section.questions);
        });
        return questions;
    }

    setupEventListeners() {
        document.getElementById('prev-btn').addEventListener('click', () => this.navigateQuestion('prev'));
        document.getElementById('next-btn').addEventListener('click', () => this.navigateQuestion('next'));
        document.getElementById('submit-btn').addEventListener('click', () => this.submitAssessment());
    }

    startAssessmentTimer(timeRemaining) {
        const timerDisplay = document.getElementById('assessment-timer');
        const updateTimer = () => {
            const minutes = Math.floor(timeRemaining / 60);
            const seconds = timeRemaining % 60;
            timerDisplay.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;
            if (timeRemaining <= 0) {
                clearInterval(timerInterval);
                this.submitAssessment();
            }
            timeRemaining--;
        };
        updateTimer();
        const timerInterval = setInterval(updateTimer, 1000);
    }

    loadQuestion(index) {
        const question = this.questions[index];
        fetch(`/assessment/api/question/${question.id}/`)
            .then(response => response.json())
            .then(data => {
                this.renderQuestion(data);
                this.updateNavigation(index);
                this.highlightCurrentQuestion(question.id);
            });
    }

    renderQuestion(questionData) {
        const container = document.getElementById('question-container');
        container.innerHTML = this.renderQuestionByType(questionData);
    }

    renderQuestionByType(question) {
        switch(question.type) {
            case 'mcq_text':
            case 'mcq_image':
            case 'mcq_mixed':
            case 'mcq_audio':
            case 'mcq_video':
            case 'mcq_paragraph':
                return this.renderMCQ(question);
            case 'fib_text':
            case 'fib_image':
            case 'fib_audio':
            case 'fib_video':
            case 'fib_paragraph':
                return this.renderFIB(question);
            // Add other question types here
            default:
                return question.text;
        }
    }

    renderMCQ(question) {
        return `
            <div class="question-content">
                <h3>${question.title}</h3>
                <div class="question-body">
                    ${question.text}
                    ${this.renderOptions(question.options)}
                </div>
            </div>
        `;
    }

    renderOptions(options) {
        return options.map(option => `
            <div>
                <input type="radio" name="option" value="${option.id}">
                ${option.text}
            </div>
        `).join('');
    }

    renderFIB(question) {
        return `
            <div class="question-content">
                <h3>${question.title}</h3>
                <div class="question-body">
                    ${this.processFIBText(question.text)}
                </div>
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

    navigateQuestion(direction) {
        this.saveCurrentAnswer();
        if (direction === 'prev' && this.currentIndex > 0) {
            this.currentIndex--;
        } else if (direction === 'next' && this.currentIndex < this.questions.length - 1) {
            this.currentIndex++;
        }
        this.loadQuestion(this.currentIndex);
    }

    saveCurrentAnswer() {
        const question = this.questions[this.currentIndex];
        const answerData = this.collectAnswerData(question.type);
        
        fetch(`/assessment/api/save-answer/${this.sessionId}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            },
            body: JSON.stringify({
                question_id: question.id,
                answer_data: answerData
            })
        });
    }

    collectAnswerData(type) {
        switch(type) {
            case 'mcq_text':
            case 'mcq_image':
            case 'mcq_mixed':
            case 'mcq_audio':
            case 'mcq_video':
            case 'mcq_paragraph':
                return document.querySelector('input[name="option"]:checked').value;
            case 'fib_text':
            case 'fib_image':
            case 'fib_audio':
            case 'fib_video':
            case 'fib_paragraph':
                return Array.from(document.querySelectorAll('.fib-input')).map(input => ({
                    blank_id: input.dataset.id,
                    value: input.value
                }));
            // Add other question types here
            default:
                return null;
        }
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

    updateNavigation(index) {
        document.getElementById('prev-btn').disabled = index === 0;
        document.getElementById('next-btn').style.display = index === this.questions.length - 1 ? 'none' : 'block';
        document.getElementById('submit-btn').style.display = index === this.questions.length - 1 ? 'block' : 'none';
    }

    highlightCurrentQuestion(questionId) {
        document.querySelectorAll('.question-item').forEach(item => {
            item.classList.remove('active');
        });
        const currentQuestion = document.querySelector(`.question-item[data-question-id="${questionId}"]`);
        if (currentQuestion) {
            currentQuestion.classList.add('active');
            currentQuestion.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
    }
}