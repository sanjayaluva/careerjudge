class AssessmentHandler {
    constructor() {
        this.questionHandler = new QuestionTypeHandler();
        this.timerHandler = new TimerHandler();
        this.currentQuestionIndex = 0;
        this.questions = [];
    }

    initialize(assessmentData) {
        this.questions = assessmentData;
        this.setupEventListeners();
        this.loadQuestion(0);
    }

    setupEventListeners() {
        document.getElementById('prev-btn').addEventListener('click', () => this.navigateQuestion('prev'));
        document.getElementById('next-btn').addEventListener('click', () => this.navigateQuestion('next'));
        document.getElementById('submit-btn').addEventListener('click', () => this.submitAssessment());
    }

    loadQuestion(index) {
        const question = this.questions[index];
        fetch(`/assessment/api/question/${question.question_id}/`)
            .then(response => response.json())
            .then(data => {
                this.renderQuestion(data);
                this.updateNavigation(index);
                this.highlightCurrentQuestion(question.question_id);
            });
    }

    renderQuestion(questionData) {
        const container = document.getElementById('question-container');
        container.innerHTML = this.questionHandler.renderQuestionByType(questionData);
        this.setupQuestionInteractions(questionData);
    }

    setupQuestionInteractions(questionData) {
        switch(questionData.type) {
            case 'cus_hotspot_single':
            case 'cus_hotspot_multiple':
                this.setupHotspotHandlers();
                break;
            case 'cus_grid':
                this.setupGridHandlers();
                break;
            case 'cus_match':
                this.setupMatchingHandlers();
                break;
            case 'psy_ranking':
                this.setupRankingHandlers();
                break;
        }
    }

    navigateQuestion(direction) {
        this.saveCurrentAnswer();
        if (direction === 'prev' && this.currentQuestionIndex > 0) {
            this.currentQuestionIndex--;
        } else if (direction === 'next' && this.currentQuestionIndex < this.questions.length - 1) {
            this.currentQuestionIndex++;
        }
        this.loadQuestion(this.currentQuestionIndex);
    }

    saveCurrentAnswer() {
        const question = this.questions[this.currentQuestionIndex];
        const answerData = this.collectAnswerData(question.type);
        
        fetch(`/assessment/api/save-answer/${sessionId}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            },
            body: JSON.stringify({
                question_id: question.question_id,
                answer_data: answerData
            })
        });
    }

    collectAnswerData(questionType) {
        const container = document.getElementById('question-container');
        switch(questionType) {
            case 'mcq_text':
            case 'mcq_image':
            case 'mcq_mixed':
            case 'mcq_audio':
            case 'mcq_video':
            case 'mcq_paragraph':
                return {
                    selected_option: container.querySelector('input[name="answer"]:checked')?.value
                };
            case 'cus_hotspot_single':
            case 'cus_hotspot_multiple':
                return {
                    selected_spots: Array.from(container.querySelectorAll('.hotspot.selected'))
                        .map(spot => spot.dataset.id)
                };
            // Add handlers for other question types
        }
    }

    submitAssessment() {
        this.saveCurrentAnswer();
        fetch(`/assessment/submit/${sessionId}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            }
        }).then(response => {
            if (response.ok) {
                window.location.href = `/assessment/results/${sessionId}/`;
            }
        });
    }
}


