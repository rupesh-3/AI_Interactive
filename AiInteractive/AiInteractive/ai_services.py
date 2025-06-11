import os
import logging
import hashlib
import re
import requests
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class AIContentProcessor:
    def __init__(self):
        self.summarizer = None
        self.qa_model = None
        self.use_transformers = False
        
        # Try to import transformers, fallback to simple methods if not available
        try:
            import torch
            from transformers import pipeline
            self.use_transformers = True
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"Transformers available, using device: {self.device}")
        except ImportError:
            logger.info("Transformers not available, using fallback methods")
            self.use_transformers = False
        
    def _load_summarizer(self):
        """Load the summarization model lazily"""
        if not self.use_transformers:
            return
            
        if self.summarizer is None:
            try:
                from transformers import pipeline
                logger.info("Loading summarization model...")
                model_name = "t5-small"
                self.summarizer = pipeline(
                    "summarization",
                    model=model_name,
                    tokenizer=model_name,
                    device=0 if self.device == "cuda" else -1,
                    framework="pt"
                )
                logger.info("Summarization model loaded successfully")
            except Exception as e:
                logger.error(f"Error loading summarization model: {str(e)}")
                self.use_transformers = False
    
    def _load_qa_model(self):
        """Load the question-answering model lazily"""
        if not self.use_transformers:
            return
            
        if self.qa_model is None:
            try:
                from transformers import pipeline
                logger.info("Loading question-answering model...")
                model_name = "t5-small"
                self.qa_model = pipeline(
                    "text2text-generation",
                    model=model_name,
                    tokenizer=model_name,
                    device=0 if self.device == "cuda" else -1,
                    framework="pt"
                )
                logger.info("Question-answering model loaded successfully")
            except Exception as e:
                logger.error(f"Error loading QA model: {str(e)}")
                self.use_transformers = False
    
    def _chunk_text(self, text, max_length=512):
        """Split text into chunks that fit the model's input length"""
        words = text.split()
        chunks = []
        current_chunk = []
        current_length = 0
        
        for word in words:
            if current_length + len(word) + 1 > max_length:
                if current_chunk:
                    chunks.append(' '.join(current_chunk))
                    current_chunk = [word]
                    current_length = len(word)
            else:
                current_chunk.append(word)
                current_length += len(word) + 1
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks
    
    def summarize_content(self, content: str, max_length: int = 150) -> str:
        """
        Generate a summary of the provided content
        """
        try:
            if not content or len(content.strip()) < 50:
                raise ValueError("Content is too short to summarize")
            
            # Clean the content
            content = re.sub(r'\s+', ' ', content.strip())
            
            if self.use_transformers:
                self._load_summarizer()
                if self.summarizer:
                    # Use transformers-based summarization
                    return self._ai_summarize(content, max_length)
            
            # Fallback to extractive summarization
            return self._extractive_summarize(content, max_length)
            
        except Exception as e:
            logger.error(f"Error in summarization: {str(e)}")
            # Final fallback
            return self._simple_summarize(content, max_length)

    def _ai_summarize(self, content: str, max_length: int) -> str:
        """AI-based summarization using transformers"""
        try:
            # Chunk the content if it's too long
            chunks = self._chunk_text(content, max_length=400)
            summaries = []
            
            for chunk in chunks:
                chunk_input = f"summarize: {chunk}"
                try:
                    summary = self.summarizer(
                        chunk_input,
                        max_length=max_length // len(chunks) if len(chunks) > 1 else max_length,
                        min_length=30,
                        do_sample=False,
                        truncation=True
                    )
                    if summary and len(summary) > 0:
                        summaries.append(summary[0]['generated_text'])
                except Exception as e:
                    logger.warning(f"Error summarizing chunk: {str(e)}")
                    continue
            
            if summaries:
                final_summary = ' '.join(summaries)
                return re.sub(r'\s+', ' ', final_summary.strip())
            else:
                raise Exception("No summaries generated")
                
        except Exception as e:
            logger.error(f"AI summarization failed: {str(e)}")
            raise

    def _extractive_summarize(self, content: str, target_words: int = 150) -> str:
        """Advanced extractive summarization using multiple ranking factors"""
        try:
            # Advanced sentence splitting handling multiple punctuation
            import string
            sentences = []
            for delimiter in ['.', '!', '?']:
                if sentences:
                    break
                temp_sentences = [s.strip() for s in content.split(delimiter) if len(s.strip()) > 15]
                if len(temp_sentences) > 1:
                    sentences = temp_sentences
            
            if not sentences:
                sentences = [s.strip() for s in content.split('.') if len(s.strip()) > 10]
            
            if not sentences:
                return content[:500] + "..."
            
            # Enhanced word frequency analysis with stopword filtering
            stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those'}
            
            word_freq = {}
            words = content.lower().split()
            total_words = len(words)
            
            for word in words:
                word = re.sub(r'[^\w]', '', word)
                if len(word) > 3 and word not in stopwords:
                    word_freq[word] = word_freq.get(word, 0) + 1
            
            # Calculate TF-IDF-like scores
            for word in word_freq:
                tf = word_freq[word] / total_words
                # Simple IDF approximation based on frequency
                idf = 1.0 / (1.0 + word_freq[word])
                word_freq[word] = tf * idf
            
            # Get top keywords
            top_keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:30]
            top_words = {word: score for word, score in top_keywords}
            
            # Advanced sentence scoring
            scored_sentences = []
            for i, sentence in enumerate(sentences):
                score = 0
                sentence_words = sentence.lower().split()
                sentence_length = len(sentence_words)
                
                # Position bonus with decay
                position_bonus = max(0, 0.5 - (i * 0.05))
                score += position_bonus
                
                # Keyword density score
                keyword_score = 0
                for word in sentence_words:
                    word = re.sub(r'[^\w]', '', word)
                    if word in top_words:
                        keyword_score += top_words[word]
                
                if sentence_length > 0:
                    keyword_density = keyword_score / sentence_length
                    score += keyword_density * 2
                
                # Length optimization (prefer medium-length sentences)
                if 15 <= sentence_length <= 35:
                    score += 0.3
                elif 10 <= sentence_length <= 45:
                    score += 0.1
                elif sentence_length < 8 or sentence_length > 50:
                    score -= 0.2
                
                # Numerical data bonus
                if any(char.isdigit() for char in sentence):
                    score += 0.15
                
                # Question bonus
                if '?' in sentence:
                    score += 0.1
                
                # Avoid sentences that are mostly capitalized (likely headers)
                caps_ratio = sum(1 for c in sentence if c.isupper()) / len(sentence)
                if caps_ratio > 0.6:
                    score -= 0.3
                
                scored_sentences.append((score, sentence, i, sentence_length))
            
            # Sort by score
            scored_sentences.sort(reverse=True)
            
            # Smart sentence selection with diversity
            selected_sentences = []
            current_words = 0
            used_indices = set()
            coverage_words = set()
            
            for score, sentence, idx, sentence_length in scored_sentences:
                if current_words + sentence_length <= target_words and idx not in used_indices:
                    # Check for content diversity
                    sentence_words = set(re.sub(r'[^\w\s]', '', sentence.lower()).split())
                    new_words = sentence_words - coverage_words
                    
                    # Prefer sentences that add new content
                    if len(new_words) > sentence_length * 0.3 or len(selected_sentences) < 2:
                        selected_sentences.append((idx, sentence))
                        used_indices.add(idx)
                        current_words += sentence_length
                        coverage_words.update(sentence_words)
                
                if current_words >= target_words * 0.85:
                    break
            
            # Ensure minimum content if too restrictive
            if len(selected_sentences) < 2 and len(scored_sentences) > 1:
                for score, sentence, idx, sentence_length in scored_sentences[:3]:
                    if idx not in used_indices and current_words + sentence_length <= target_words * 1.2:
                        selected_sentences.append((idx, sentence))
                        used_indices.add(idx)
                        current_words += sentence_length
            
            # Sort selected sentences by original order
            selected_sentences.sort()
            summary = '. '.join([sentence for _, sentence in selected_sentences])
            
            if summary:
                # Clean up the summary
                summary = re.sub(r'\s+', ' ', summary.strip())
                return summary + ('.' if not summary.endswith('.') else '')
            else:
                return sentences[0] + '.'
                
        except Exception as e:
            logger.error(f"Advanced extractive summarization failed: {str(e)}")
            # Fallback to simple method
            return self._simple_extractive_fallback(content, target_words)

    def _simple_extractive_fallback(self, content: str, target_words: int) -> str:
        """Simple fallback for extractive summarization"""
        sentences = [s.strip() for s in content.split('.') if len(s.strip()) > 10]
        if not sentences:
            return content[:500] + "..."
        
        # Take first few sentences up to target word count
        selected = []
        word_count = 0
        for sentence in sentences[:5]:
            sentence_words = len(sentence.split())
            if word_count + sentence_words <= target_words:
                selected.append(sentence)
                word_count += sentence_words
            else:
                break
        
        return '. '.join(selected) + '.' if selected else sentences[0] + '.'

    def _simple_summarize(self, content: str, target_words: int = 150) -> str:
        """Simple fallback summarization"""
        try:
            words = content.split()
            if len(words) <= target_words:
                return content
            
            # Take first part and try to end at sentence boundary
            truncated = ' '.join(words[:target_words])
            last_period = truncated.rfind('.')
            
            if last_period > target_words // 2:
                return truncated[:last_period + 1]
            else:
                return truncated + '...'
                
        except Exception:
            return "Unable to generate summary from the provided content."
    
    def answer_question(self, question: str, context: str, word_count: int = 100, complexity: str = "medium") -> str:
        """
        Answer a question based on the provided context
        """
        try:
            if not question or not context:
                raise ValueError("Question and context are required")
            
            if self.use_transformers:
                self._load_qa_model()
                if self.qa_model:
                    return self._ai_answer_question(question, context, word_count, complexity)
            
            # Fallback to extractive Q&A
            return self._extract_relevant_context(question, context, word_count)
                
        except Exception as e:
            logger.error(f"Error in question answering: {str(e)}")
            return self._extract_relevant_context(question, context, word_count)

    def _ai_answer_question(self, question: str, context: str, word_count: int, complexity: str) -> str:
        """AI-based question answering using transformers"""
        try:
            # Construct the input for T5
            input_text = f"question: {question} context: {context[:800]}"
            
            # Generate answer
            max_answer_length = min(word_count * 2, 200)
            
            answer = self.qa_model(
                input_text,
                max_length=max_answer_length,
                min_length=max(10, word_count // 2),
                do_sample=True,
                temperature=0.7,
                truncation=True
            )
            
            if answer and len(answer) > 0:
                generated_answer = answer[0]['generated_text']
                generated_answer = re.sub(r'\s+', ' ', generated_answer.strip())
                
                # Limit to requested word count
                words = generated_answer.split()
                if len(words) > word_count * 1.5:
                    generated_answer = ' '.join(words[:int(word_count * 1.2)])
                
                return generated_answer
            else:
                raise Exception("No answer generated")
                
        except Exception as e:
            logger.error(f"AI answer generation failed: {str(e)}")
            raise
    
    def _extract_relevant_context(self, question: str, context: str, word_count: int) -> str:
        """
        Advanced context extraction for question answering with multiple strategies
        """
        try:
            # Clean and prepare question
            question_lower = question.lower().strip()
            question_words = set(re.sub(r'[^\w\s]', '', question_lower).split())
            
            # Remove question words and common stopwords
            stopwords = {'what', 'who', 'when', 'where', 'why', 'how', 'is', 'are', 'was', 'were', 'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
            question_keywords = question_words - stopwords
            
            # Enhanced sentence splitting
            sentences = []
            for delimiter in ['.', '!', '?']:
                temp_sentences = [s.strip() for s in context.split(delimiter) if len(s.strip()) > 10]
                if len(temp_sentences) > len(sentences):
                    sentences = temp_sentences
            
            if not sentences:
                sentences = [context[:500]]
            
            # Advanced scoring system
            scored_sentences = []
            for i, sentence in enumerate(sentences):
                sentence_lower = sentence.lower()
                sentence_words = set(re.sub(r'[^\w\s]', '', sentence_lower).split())
                sentence_length = len(sentence.split())
                
                # Base relevance score
                exact_matches = len(question_keywords.intersection(sentence_words))
                partial_matches = 0
                
                # Check for partial word matches
                for q_word in question_keywords:
                    if len(q_word) > 4:
                        for s_word in sentence_words:
                            if q_word in s_word or s_word in q_word:
                                partial_matches += 0.5
                
                # Question type specific scoring
                question_type_bonus = 0
                if any(qw in question_lower for qw in ['what is', 'what are']):
                    if any(phrase in sentence_lower for phrase in ['is', 'are', 'means', 'refers to', 'defined as']):
                        question_type_bonus += 0.5
                elif any(qw in question_lower for qw in ['how', 'how to']):
                    if any(phrase in sentence_lower for phrase in ['process', 'method', 'steps', 'procedure', 'way']):
                        question_type_bonus += 0.5
                elif any(qw in question_lower for qw in ['why', 'reason']):
                    if any(phrase in sentence_lower for phrase in ['because', 'due to', 'reason', 'cause', 'result']):
                        question_type_bonus += 0.5
                elif any(qw in question_lower for qw in ['when', 'time']):
                    if any(char.isdigit() for char in sentence) or any(month in sentence_lower for month in ['january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december']):
                        question_type_bonus += 0.5
                
                # Position bonus (earlier sentences often contain key information)
                position_bonus = max(0, 0.3 - (i * 0.02))
                
                # Length optimization
                length_bonus = 0
                if 10 <= sentence_length <= 40:
                    length_bonus = 0.2
                elif sentence_length < 5:
                    length_bonus = -0.3
                
                # Calculate final score
                total_score = (exact_matches * 1.0) + (partial_matches * 0.5) + question_type_bonus + position_bonus + length_bonus
                
                if total_score > 0:
                    scored_sentences.append((total_score, sentence, i, sentence_length))
            
            # Sort by relevance score
            scored_sentences.sort(reverse=True)
            
            if not scored_sentences:
                # Fallback: return first meaningful sentences
                meaningful_sentences = [s for s in sentences[:3] if len(s.split()) >= 8]
                if meaningful_sentences:
                    words_so_far = 0
                    result = []
                    for sentence in meaningful_sentences:
                        words_in_sentence = len(sentence.split())
                        if words_so_far + words_in_sentence <= word_count:
                            result.append(sentence)
                            words_so_far += words_in_sentence
                        else:
                            break
                    return '. '.join(result) + '.' if result else meaningful_sentences[0] + '.'
                else:
                    words = context.split()[:word_count]
                    return ' '.join(words) + '...'
            
            # Select best sentences with diversity
            result_sentences = []
            current_word_count = 0
            used_content = set()
            
            for score, sentence, idx, sentence_length in scored_sentences:
                if current_word_count + sentence_length <= word_count:
                    # Check for content diversity
                    sentence_words = set(sentence.lower().split()[:10])  # Check first 10 words for uniqueness
                    overlap = len(sentence_words.intersection(used_content))
                    
                    # Include if minimal overlap or if we have very few sentences
                    if overlap < 3 or len(result_sentences) < 2:
                        result_sentences.append((idx, sentence))
                        current_word_count += sentence_length
                        used_content.update(sentence_words)
                
                if current_word_count >= word_count * 0.8:
                    break
            
            # Sort by original order to maintain coherence
            result_sentences.sort()
            
            if result_sentences:
                answer = '. '.join([sentence for _, sentence in result_sentences])
                # Clean up the answer
                answer = re.sub(r'\s+', ' ', answer.strip())
                return answer + ('.' if not answer.endswith('.') else '')
            else:
                # Final fallback
                words = context.split()[:word_count]
                return ' '.join(words) + '...'
                
        except Exception as e:
            logger.error(f"Error in advanced context extraction: {str(e)}")
            return self._simple_qa_fallback(question, context, word_count)

    def _simple_qa_fallback(self, question: str, context: str, word_count: int) -> str:
        """Simple fallback for Q&A when advanced methods fail"""
        try:
            question_words = question.lower().split()
            sentences = context.split('.')[:10]  # First 10 sentences
            
            best_sentence = ""
            best_score = 0
            
            for sentence in sentences:
                if len(sentence.strip()) > 10:
                    sentence_words = sentence.lower().split()
                    score = sum(1 for word in question_words if word in sentence_words)
                    if score > best_score:
                        best_score = score
                        best_sentence = sentence.strip()
            
            if best_sentence:
                words = best_sentence.split()
                if len(words) > word_count:
                    return ' '.join(words[:word_count]) + '...'
                return best_sentence + '.'
            else:
                words = context.split()[:word_count]
                return ' '.join(words) + '...'
                
        except Exception:
            return "I couldn't find a specific answer to your question in the provided content."
    
    def get_content_hash(self, content: str) -> str:
        """Generate a hash for content caching"""
        return hashlib.md5(content.encode()).hexdigest()

# Global instance
ai_processor = AIContentProcessor()
