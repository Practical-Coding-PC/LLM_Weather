import React, { useState } from "react";
import axios from "axios";

function App() {
  const handleGenerateQuestion = async () => {
    try {
      console.log("first")
      const response = await axios.post("http://localhost:5001/api/weather~~",
        {
          job_role: jobRole
        },
        {
          headers: {"Content-Type": "application/json"},
          withCredentials: true
        });
      console.log(response.data)
      setQuestions(response.data.questions);
    } catch (error) {
      console.error("Error generating questions:", error);
    }
  };

  return (
    <div className="App">
      <h1>AI 면접 질문 생성</h1>
      <input
        type="text"
        value={jobRole}
        onChange={(e) => setJobRole(e.target.value)}
        placeholder="직군을 입력하세요"
      />
      <button onClick={handleGenerateQuestion}>질문 생성</button>

      <div>
        {questions.length > 0 && (
          <ul>
            {questions.map((question, index) => (
              <li key={index}>{question}</li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

export default App;
