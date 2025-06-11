from flask import render_template, request, redirect, url_for, flash, jsonify
from app import app, db
from models import ContentAnalysis, QuestionAnswer
from web_scraper import get_website_text_content, validate_url
from ai_services import ai_processor
from accuracy_monitor import accuracy_monitor
import logging

logger = logging.getLogger(__name__)

@app.route('/')
def index():
    """Main page with URL input form"""
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze_content():
    """Process URL and generate summary"""
    try:
        url = request.form.get('url', '').strip()
        
        if not url:
            flash('Please provide a URL to analyze.', 'error')
            return redirect(url_for('index'))
        
        if not validate_url(url):
            flash('Please provide a valid URL.', 'error')
            return redirect(url_for('index'))
        
        # Extract content from URL
        try:
            content_data = get_website_text_content(url)
        except Exception as e:
            flash(f'Error fetching content: {str(e)}', 'error')
            return redirect(url_for('index'))
        
        # Check if we already have this content analyzed
        content_hash = ai_processor.get_content_hash(content_data['content'])
        existing_analysis = ContentAnalysis.query.filter_by(content_hash=content_hash).first()
        
        if existing_analysis:
            logger.info(f"Using cached analysis for URL: {url}")
            return render_template('results.html', 
                                 analysis=existing_analysis,
                                 content_data=content_data)
        
        # Generate summary
        try:
            summary = ai_processor.summarize_content(content_data['content'])
            
            # Evaluate summary quality
            quality_metrics = accuracy_monitor.evaluate_summary_quality(
                content_data['content'], 
                summary, 
                url
            )
            
            # Log quality metrics
            logger.info(f"Summary quality score: {quality_metrics.get('overall_score', 0):.2f} for {url}")
            
        except Exception as e:
            flash(f'Error generating summary: {str(e)}', 'error')
            return redirect(url_for('index'))
        
        # Save analysis to database
        analysis = ContentAnalysis(
            url=url,
            title=content_data['title'],
            content_hash=content_hash,
            summary=summary,
            original_content=content_data['content']
        )
        
        try:
            db.session.add(analysis)
            db.session.commit()
            logger.info(f"Saved analysis for URL: {url}")
        except Exception as e:
            logger.error(f"Error saving analysis: {str(e)}")
            db.session.rollback()
        
        return render_template('results.html', 
                             analysis=analysis,
                             content_data=content_data)
        
    except Exception as e:
        logger.error(f"Unexpected error in analyze_content: {str(e)}")
        flash('An unexpected error occurred. Please try again.', 'error')
        return redirect(url_for('index'))

@app.route('/ask_question', methods=['POST'])
def ask_question():
    """Process question about analyzed content"""
    try:
        analysis_id = request.form.get('analysis_id')
        question = request.form.get('question', '').strip()
        word_count = request.form.get('word_count', '100')
        complexity = request.form.get('complexity', 'medium')
        
        if not analysis_id or not question:
            flash('Analysis ID and question are required.', 'error')
            return redirect(url_for('index'))
        
        # Validate word count
        try:
            word_count = int(word_count)
            if word_count < 10 or word_count > 500:
                word_count = 100
        except (ValueError, TypeError):
            word_count = 100
        
        # Get the analysis
        analysis = ContentAnalysis.query.get_or_404(analysis_id)
        
        # Check for existing answer
        existing_qa = QuestionAnswer.query.filter_by(
            content_analysis_id=analysis_id,
            question=question,
            word_count_preference=word_count,
            complexity_level=complexity
        ).first()
        
        if existing_qa:
            logger.info(f"Using cached answer for question: {question[:50]}...")
            return render_template('results.html', 
                                 analysis=analysis,
                                 question_answer=existing_qa,
                                 show_qa=True)
        
        # Generate answer
        try:
            answer = ai_processor.answer_question(
                question=question,
                context=analysis.original_content,
                word_count=word_count,
                complexity=complexity
            )
            
            # Evaluate Q&A quality
            qa_quality_metrics = accuracy_monitor.evaluate_qa_quality(
                question=question,
                answer=answer,
                context=analysis.original_content,
                url=analysis.url
            )
            
            # Log quality metrics
            logger.info(f"Q&A quality score: {qa_quality_metrics.get('overall_score', 0):.2f} for question: {question[:50]}...")
            
        except Exception as e:
            flash(f'Error generating answer: {str(e)}', 'error')
            return render_template('results.html', analysis=analysis)
        
        # Save Q&A to database
        qa = QuestionAnswer(
            content_analysis_id=analysis.id,
            question=question,
            answer=answer,
            word_count_preference=word_count,
            complexity_level=complexity
        )
        
        try:
            db.session.add(qa)
            db.session.commit()
            logger.info(f"Saved Q&A for analysis ID: {analysis_id}")
        except Exception as e:
            logger.error(f"Error saving Q&A: {str(e)}")
            db.session.rollback()
        
        return render_template('results.html', 
                             analysis=analysis,
                             question_answer=qa,
                             show_qa=True)
        
    except Exception as e:
        logger.error(f"Unexpected error in ask_question: {str(e)}")
        flash('An unexpected error occurred while processing your question.', 'error')
        return redirect(url_for('index'))

@app.route('/history')
def history():
    """Show analysis history"""
    try:
        analyses = ContentAnalysis.query.order_by(ContentAnalysis.created_at.desc()).limit(50).all()
        return render_template('history.html', analyses=analyses)
    except Exception as e:
        logger.error(f"Error loading history: {str(e)}")
        flash('Error loading history.', 'error')
        return redirect(url_for('index'))

@app.route('/analysis/<int:analysis_id>')
def view_analysis(analysis_id):
    """View a specific analysis"""
    try:
        analysis = ContentAnalysis.query.get_or_404(analysis_id)
        return render_template('results.html', analysis=analysis)
    except Exception as e:
        logger.error(f"Error viewing analysis {analysis_id}: {str(e)}")
        flash('Analysis not found.', 'error')
        return redirect(url_for('index'))

@app.route('/performance')
def performance_dashboard():
    """Performance monitoring dashboard"""
    try:
        performance_summary = accuracy_monitor.get_performance_summary()
        return render_template('performance.html', performance=performance_summary)
    except Exception as e:
        logger.error(f"Error loading performance dashboard: {str(e)}")
        flash('Error loading performance data.', 'error')
        return redirect(url_for('index'))

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500
