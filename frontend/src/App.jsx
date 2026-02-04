import { useState, useEffect } from "react";
import axios from "axios";
import "./App.css";

function App() {
  const [tasks, setTasks] = useState([]);
  const [newTask, setNewTask] = useState("");

  const API_URL = "https://smart-todo-backend-ld93.onrender.com/api/tasks/";

  const fetchTasks = () => {
    axios
      .get(API_URL)
      .then((response) => setTasks(response.data))
      .catch((error) => console.error("Error fetching data:", error));
  };

  useEffect(() => {
    fetchTasks();
  }, []);

  const addTask = () => {
    if (!newTask) return;
    axios
      .post(API_URL, {
        title: newTask,
        status: "Pending",
        priority: "Medium"
      })
      .then((response) => {
        setTasks([...tasks, response.data]);
        setNewTask("");
      })
      .catch((error) => console.error("Error adding task:", error));
  };

  const deleteTask = (id) => {
    axios
      .delete(`${API_URL}${id}/`)
      .then(() => {
        setTasks(tasks.filter((task) => task.id !== id));
      })
      .catch((error) => console.error("Error deleting task:", error));
  };

  const toggleStatus = (id, currentStatus) => {
    const newStatus = currentStatus === "Pending" ? "Completed" : "Pending";
    axios
      .patch(`${API_URL}${id}/`, { status: newStatus })
      .then((response) => {
        setTasks(tasks.map((task) => (task.id === id ? response.data : task)));
      })
      .catch((error) => console.error("Error updating task:", error));
  };

  return (
    <div className="app-container">
      <h1>My Smart Todo List</h1>

      <div className="input-section">
        <input
          type="text"
          placeholder="Try: 'Call Dad tomorrow at 10am'"
          value={newTask}
          onChange={(e) => setNewTask(e.target.value)}
          className="task-input"
          onKeyDown={(e) => e.key === 'Enter' && addTask()}
        />
        <button onClick={addTask} className="add-button">Add</button>
      </div>

      <div className="task-list">
        {tasks.map((task) => (
          <div key={task.id} className="task-card">
            <div className="task-info">
              <div className="task-text">
                <h3>{task.title}</h3>
                
                {/* USE THE SERVER STRING DIRECTLY - NO MATH */}
                {task.formatted_date && (
                    <span className="due-date">⏰ {task.formatted_date}</span>
                )}
                
                <div className="badges">
                    <span className={`badge priority ${task.priority.toLowerCase()}`}>
                    {task.priority}
                    </span>
                    <span className={`badge status ${task.status.toLowerCase()}`}>
                    {task.status}
                    </span>
                </div>
              </div>
              
              <div className="action-buttons">
                <button onClick={() => toggleStatus(task.id, task.status)} className="check-btn">
                  {task.status === "Pending" ? "✅" : "↩️"}
                </button>
                <button onClick={() => deleteTask(task.id)} className="delete-btn">
                  🗑️
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default App;
