from app import db
from datetime import datetime

class ContentAnalysis(db.Model):
    """Model to store content analysis results for caching and history"""
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(500), nullable=False)
    title = db.Column(db.String(200))
    content_hash = db.Column(db.String(64), nullable=False)  # Hash of the content for caching
    summary = db.Column(db.Text)
    original_content = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<ContentAnalysis {self.url}>'

class QuestionAnswer(db.Model):
    """Model to store question-answer pairs for a given content"""
    id = db.Column(db.Integer, primary_key=True)
    content_analysis_id = db.Column(db.Integer, db.ForeignKey('content_analysis.id'), nullable=False)
    question = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text, nullable=False)
    word_count_preference = db.Column(db.Integer)
    complexity_level = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    content_analysis = db.relationship('ContentAnalysis', backref=db.backref('questions', lazy=True))
    
    def __repr__(self):
        return f'<QuestionAnswer {self.question[:50]}...>'
