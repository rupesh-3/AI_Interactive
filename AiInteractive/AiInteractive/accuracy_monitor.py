import logging
import time
import json
from datetime import datetime
from typing import Dict, List, Tuple, Any
import re

logger = logging.getLogger(__name__)

class AccuracyMonitor:
    """
    Monitor and evaluate AI model accuracy for summarization and Q&A
    Implements metrics for achieving 90% accuracy target
    """
    
    def __init__(self):
        self.performance_logs = []
        self.accuracy_thresholds = {
            'summarization': 0.90,
            'qa': 0.90
        }
        self.rouge_scores = {}
        self.qa_scores = {}
        
    def evaluate_summary_quality(self, original_content: str, summary: str, url: str = None) -> Dict[str, float]:
        """
        Evaluate summary quality using multiple metrics
        Returns scores for different quality aspects
        """
        try:
            start_time = time.time()
            
            # Content coverage score
            coverage_score = self._calculate_coverage_score(original_content, summary)
            
            # Coherence and readability score
            coherence_score = self._calculate_coherence_score(summary)
            
            # Compression ratio (ideal range: 5-15%)
            compression_ratio = len(summary.split()) / len(original_content.split())
            compression_score = self._evaluate_compression_ratio(compression_ratio)
            
            # Key information preservation
            key_info_score = self._calculate_key_info_preservation(original_content, summary)
            
            # Overall quality score (weighted average)
            overall_score = (
                coverage_score * 0.3 +
                coherence_score * 0.25 +
                compression_score * 0.2 +
                key_info_score * 0.25
            )
            
            processing_time = time.time() - start_time
            
            result = {
                'overall_score': overall_score,
                'coverage_score': coverage_score,
                'coherence_score': coherence_score,
                'compression_score': compression_score,
                'key_info_score': key_info_score,
                'compression_ratio': compression_ratio,
                'processing_time': processing_time,
                'meets_threshold': overall_score >= self.accuracy_thresholds['summarization']
            }
            
            # Log performance
            self._log_performance('summarization', url, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error evaluating summary quality: {str(e)}")
            return {'overall_score': 0.0, 'error': str(e)}
    
    def evaluate_qa_quality(self, question: str, answer: str, context: str, url: str = None) -> Dict[str, float]:
        """
        Evaluate Q&A response quality using multiple metrics
        Returns scores for different quality aspects
        """
        try:
            start_time = time.time()
            
            # Relevance score (how well answer addresses question)
            relevance_score = self._calculate_qa_relevance(question, answer, context)
            
            # Factual accuracy score (based on context grounding)
            accuracy_score = self._calculate_factual_accuracy(answer, context)
            
            # Completeness score (does answer fully address question)
            completeness_score = self._calculate_completeness(question, answer)
            
            # Coherence and clarity score
            coherence_score = self._calculate_coherence_score(answer)
            
            # Context utilization score
            context_score = self._calculate_context_utilization(answer, context)
            
            # Overall quality score (weighted average)
            overall_score = (
                relevance_score * 0.3 +
                accuracy_score * 0.25 +
                completeness_score * 0.2 +
                coherence_score * 0.15 +
                context_score * 0.1
            )
            
            processing_time = time.time() - start_time
            
            result = {
                'overall_score': overall_score,
                'relevance_score': relevance_score,
                'accuracy_score': accuracy_score,
                'completeness_score': completeness_score,
                'coherence_score': coherence_score,
                'context_score': context_score,
                'processing_time': processing_time,
                'meets_threshold': overall_score >= self.accuracy_thresholds['qa']
            }
            
            # Log performance
            self._log_performance('qa', url, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Error evaluating Q&A quality: {str(e)}")
            return {'overall_score': 0.0, 'error': str(e)}
    
    def _calculate_coverage_score(self, original: str, summary: str) -> float:
        """Calculate how well summary covers key content"""
        try:
            # Extract key terms from original content
            original_words = set(re.sub(r'[^\w\s]', '', original.lower()).split())
            summary_words = set(re.sub(r'[^\w\s]', '', summary.lower()).split())
            
            # Remove common stopwords
            stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had'}
            
            original_keywords = {word for word in original_words if len(word) > 3 and word not in stopwords}
            summary_keywords = {word for word in summary_words if len(word) > 3 and word not in stopwords}
            
            if not original_keywords:
                return 0.5
            
            # Calculate coverage
            covered_keywords = len(original_keywords.intersection(summary_keywords))
            coverage_ratio = covered_keywords / len(original_keywords)
            
            # Score between 0 and 1
            return min(1.0, coverage_ratio * 1.5)  # Boost score since perfect coverage isn't expected
            
        except Exception as e:
            logger.error(f"Error calculating coverage score: {str(e)}")
            return 0.5
    
    def _calculate_coherence_score(self, text: str) -> float:
        """Calculate text coherence and readability"""
        try:
            sentences = [s.strip() for s in text.split('.') if len(s.strip()) > 5]
            if not sentences:
                return 0.0
            
            score = 0.8  # Base score
            
            # Check sentence length variety
            lengths = [len(s.split()) for s in sentences]
            if lengths:
                avg_length = sum(lengths) / len(lengths)
                # Prefer moderate sentence lengths (10-25 words)
                if 10 <= avg_length <= 25:
                    score += 0.1
                elif avg_length < 5 or avg_length > 40:
                    score -= 0.2
            
            # Check for proper punctuation and capitalization
            if text.strip().endswith('.'):
                score += 0.05
            
            # Check for repetition
            words = text.lower().split()
            unique_words = set(words)
            repetition_ratio = len(unique_words) / len(words) if words else 0
            if repetition_ratio > 0.7:
                score += 0.05
            elif repetition_ratio < 0.5:
                score -= 0.1
            
            return max(0.0, min(1.0, score))
            
        except Exception as e:
            logger.error(f"Error calculating coherence score: {str(e)}")
            return 0.5
    
    def _evaluate_compression_ratio(self, ratio: float) -> float:
        """Evaluate if compression ratio is appropriate"""
        # Ideal compression: 5-15% of original content
        if 0.05 <= ratio <= 0.15:
            return 1.0
        elif 0.03 <= ratio <= 0.25:
            return 0.8
        elif 0.01 <= ratio <= 0.35:
            return 0.6
        else:
            return 0.3
    
    def _calculate_key_info_preservation(self, original: str, summary: str) -> float:
        """Check if key information is preserved"""
        try:
            # Look for numbers, dates, names (capitalized words), and key phrases
            import re
            
            # Extract numbers and dates
            original_numbers = set(re.findall(r'\b\d+(?:\.\d+)?\b', original))
            summary_numbers = set(re.findall(r'\b\d+(?:\.\d+)?\b', summary))
            
            # Extract capitalized words (potential names/places)
            original_caps = set(re.findall(r'\b[A-Z][a-z]+\b', original))
            summary_caps = set(re.findall(r'\b[A-Z][a-z]+\b', summary))
            
            # Calculate preservation ratios
            number_preservation = 0.5
            if original_numbers:
                number_preservation = len(summary_numbers.intersection(original_numbers)) / len(original_numbers)
            
            caps_preservation = 0.5
            if original_caps:
                caps_preservation = len(summary_caps.intersection(original_caps)) / len(original_caps)
            
            # Weight the scores
            overall_preservation = (number_preservation * 0.4) + (caps_preservation * 0.6)
            
            return min(1.0, overall_preservation * 1.2)  # Slight boost since perfect preservation isn't expected
            
        except Exception as e:
            logger.error(f"Error calculating key info preservation: {str(e)}")
            return 0.5
    
    def _calculate_qa_relevance(self, question: str, answer: str, context: str) -> float:
        """Calculate how relevant the answer is to the question"""
        try:
            question_words = set(re.sub(r'[^\w\s]', '', question.lower()).split())
            answer_words = set(re.sub(r'[^\w\s]', '', answer.lower()).split())
            
            # Remove question words and stopwords
            stopwords = {'what', 'who', 'when', 'where', 'why', 'how', 'is', 'are', 'was', 'were', 'the', 'a', 'an', 'and', 'or', 'but'}
            question_keywords = question_words - stopwords
            
            if not question_keywords:
                return 0.7  # Default score for generic questions
            
            # Check keyword overlap
            keyword_overlap = len(question_keywords.intersection(answer_words)) / len(question_keywords)
            
            # Check question type alignment
            type_score = self._check_question_type_alignment(question, answer)
            
            # Combine scores
            relevance_score = (keyword_overlap * 0.6) + (type_score * 0.4)
            
            return min(1.0, relevance_score)
            
        except Exception as e:
            logger.error(f"Error calculating Q&A relevance: {str(e)}")
            return 0.5
    
    def _check_question_type_alignment(self, question: str, answer: str) -> float:
        """Check if answer type matches question type"""
        question_lower = question.lower()
        answer_lower = answer.lower()
        
        # What questions expect definitions/explanations
        if any(phrase in question_lower for phrase in ['what is', 'what are', 'what does']):
            if any(phrase in answer_lower for phrase in ['is', 'are', 'means', 'refers to']):
                return 1.0
            return 0.6
        
        # How questions expect processes/methods
        elif any(phrase in question_lower for phrase in ['how', 'how to', 'how does']):
            if any(phrase in answer_lower for phrase in ['by', 'through', 'process', 'method', 'step']):
                return 1.0
            return 0.6
        
        # Why questions expect reasons/causes
        elif any(phrase in question_lower for phrase in ['why', 'reason']):
            if any(phrase in answer_lower for phrase in ['because', 'due to', 'reason', 'cause']):
                return 1.0
            return 0.6
        
        # When questions expect time references
        elif any(phrase in question_lower for phrase in ['when', 'time']):
            if any(char.isdigit() for char in answer) or any(word in answer_lower for word in ['year', 'month', 'day', 'century']):
                return 1.0
            return 0.6
        
        return 0.8  # Default score for other question types
    
    def _calculate_factual_accuracy(self, answer: str, context: str) -> float:
        """Calculate factual accuracy based on context grounding"""
        try:
            answer_words = set(re.sub(r'[^\w\s]', '', answer.lower()).split())
            context_words = set(re.sub(r'[^\w\s]', '', context.lower()).split())
            
            # Check if answer content is grounded in context
            grounded_words = answer_words.intersection(context_words)
            if not answer_words:
                return 0.5
            
            grounding_ratio = len(grounded_words) / len(answer_words)
            
            # Check for potential hallucinations (specific facts not in context)
            import re
            answer_numbers = set(re.findall(r'\b\d+(?:\.\d+)?\b', answer))
            context_numbers = set(re.findall(r'\b\d+(?:\.\d+)?\b', context))
            
            number_accuracy = 1.0
            if answer_numbers:
                ungrounded_numbers = answer_numbers - context_numbers
                if ungrounded_numbers:
                    number_accuracy = max(0.3, 1.0 - (len(ungrounded_numbers) / len(answer_numbers)))
            
            # Combine scores
            overall_accuracy = (grounding_ratio * 0.7) + (number_accuracy * 0.3)
            
            return min(1.0, overall_accuracy)
            
        except Exception as e:
            logger.error(f"Error calculating factual accuracy: {str(e)}")
            return 0.5
    
    def _calculate_completeness(self, question: str, answer: str) -> float:
        """Calculate if answer completely addresses the question"""
        try:
            # Basic length check
            answer_length = len(answer.split())
            
            # Very short answers are likely incomplete
            if answer_length < 10:
                return 0.4
            elif answer_length < 20:
                return 0.7
            else:
                return 0.9
            
        except Exception as e:
            logger.error(f"Error calculating completeness: {str(e)}")
            return 0.5
    
    def _calculate_context_utilization(self, answer: str, context: str) -> float:
        """Calculate how well the answer utilizes the context"""
        try:
            answer_words = set(answer.lower().split())
            context_words = set(context.lower().split())
            
            if not answer_words:
                return 0.0
            
            utilized_words = answer_words.intersection(context_words)
            utilization_ratio = len(utilized_words) / len(answer_words)
            
            return min(1.0, utilization_ratio * 1.2)  # Slight boost
            
        except Exception as e:
            logger.error(f"Error calculating context utilization: {str(e)}")
            return 0.5
    
    def _log_performance(self, task_type: str, url: str, metrics: Dict[str, Any]):
        """Log performance metrics for analysis"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'task_type': task_type,
            'url': url,
            'metrics': metrics
        }
        
        self.performance_logs.append(log_entry)
        
        # Keep only last 1000 entries
        if len(self.performance_logs) > 1000:
            self.performance_logs = self.performance_logs[-1000:]
        
        # Log significant performance issues
        if metrics.get('overall_score', 0) < 0.7:
            logger.warning(f"Low quality {task_type} output: {metrics.get('overall_score', 0):.2f} for {url}")
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get overall performance summary"""
        try:
            if not self.performance_logs:
                return {'message': 'No performance data available'}
            
            summary_logs = [log for log in self.performance_logs if log['task_type'] == 'summarization']
            qa_logs = [log for log in self.performance_logs if log['task_type'] == 'qa']
            
            summary_stats = self._calculate_task_stats(summary_logs, 'summarization')
            qa_stats = self._calculate_task_stats(qa_logs, 'qa')
            
            return {
                'total_operations': len(self.performance_logs),
                'summarization': summary_stats,
                'qa': qa_stats,
                'overall_accuracy': (summary_stats.get('avg_score', 0) + qa_stats.get('avg_score', 0)) / 2 if summary_stats and qa_stats else 0,
                'meets_90_percent_target': summary_stats.get('avg_score', 0) >= 0.9 and qa_stats.get('avg_score', 0) >= 0.9
            }
            
        except Exception as e:
            logger.error(f"Error generating performance summary: {str(e)}")
            return {'error': str(e)}
    
    def _calculate_task_stats(self, logs: List[Dict], task_type: str) -> Dict[str, Any]:
        """Calculate statistics for a specific task type"""
        if not logs:
            return {}
        
        scores = [log['metrics'].get('overall_score', 0) for log in logs]
        meeting_threshold = [log['metrics'].get('meets_threshold', False) for log in logs]
        
        return {
            'total_operations': len(logs),
            'avg_score': sum(scores) / len(scores),
            'min_score': min(scores),
            'max_score': max(scores),
            'accuracy_rate': sum(meeting_threshold) / len(meeting_threshold),
            'meets_target': sum(meeting_threshold) / len(meeting_threshold) >= 0.9
        }

# Global accuracy monitor instance
accuracy_monitor = AccuracyMonitor()