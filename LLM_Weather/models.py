from db import db

class InterviewRecord(db.Model):
    __tablename__ = "interview_records"

    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text, nullable=True)
    feedback = db.Column(db.Text, nullable=True)