import { useState, useEffect } from "react";
import "./App.css";
import { BrowserRouter, Routes, Route, Link } from "react-router-dom";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const VNCManager = () => {
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [newSession, setNewSession] = useState({
    display_id: 1,
    geometry: "1280x720"
  });

  const fetchSessions = async () => {
    try {
      const response = await axios.get(`${API}/vnc/sessions`);
      setSessions(response.data);
    } catch (e) {
      console.error("Error fetching VNC sessions:", e);
    }
  };

  useEffect(() => {
    fetchSessions();
  }, []);

  const createSession = async () => {
    setLoading(true);
    try {
      const response = await axios.post(`${API}/vnc/sessions`, newSession);
      console.log("VNC session created:", response.data);
      await fetchSessions();
      setNewSession({ display_id: newSession.display_id + 1, geometry: "1280x720" });
    } catch (e) {
      console.error("Error creating VNC session:", e);
      alert("Ошибка создания VNC сессии: " + (e.response?.data?.detail || e.message));
    }
    setLoading(false);
  };

  const deleteSession = async (sessionId) => {
    try {
      await axios.delete(`${API}/vnc/sessions/${sessionId}`);
      await fetchSessions();
    } catch (e) {
      console.error("Error deleting VNC session:", e);
      alert("Ошибка удаления сессии: " + (e.response?.data?.detail || e.message));
    }
  };

  const getConnectionInfo = async (sessionId) => {
    try {
      const response = await axios.get(`${API}/vnc/connect/${sessionId}`);
      const info = response.data;
      
      // Создаем модальное окно с информацией о подключении
      const modal = document.createElement('div');
      modal.style.cssText = `
        position: fixed; top: 0; left: 0; width: 100%; height: 100%;
        background: rgba(0,0,0,0.8); display: flex; align-items: center;
        justify-content: center; z-index: 1000;
      `;
      
      modal.innerHTML = `
        <div style="background: white; padding: 30px; border-radius: 10px; max-width: 600px; width: 90%;">
          <h2 style="margin-top: 0; color: #333;">🖥️ VNC Connection Info</h2>
          <div style="margin: 20px 0;">
            <p><strong>Display ID:</strong> ${info.display_id}</p>
            <p><strong>VNC Port:</strong> ${info.vnc_url}</p>
            <p><strong>WebSocket URL:</strong> ${info.websocket_url}</p>
            <p><strong>Password:</strong> vncpass</p>
          </div>
          <div style="margin: 20px 0;">
            <h3>🌐 Web VNC Access:</h3>
            <a href="${info.novnc_url}" target="_blank" 
               style="display: inline-block; background: #007bff; color: white; padding: 10px 20px; 
                      border-radius: 5px; text-decoration: none; margin: 10px 0;">
              🚀 Open VNC in Browser
            </a>
          </div>
          <button onclick="this.parentElement.parentElement.remove()" 
                  style="background: #dc3545; color: white; border: none; padding: 10px 20px; 
                         border-radius: 5px; cursor: pointer; float: right;">
            Close
          </button>
        </div>
      `;
      
      document.body.appendChild(modal);
      modal.onclick = (e) => {
        if (e.target === modal) modal.remove();
      };
      
    } catch (e) {
      console.error("Error getting connection info:", e);
      alert("Ошибка получения информации о подключении");
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-3xl font-bold text-gray-800 mb-8">🖥️ VNC Session Manager</h1>
        
        {/* Create New Session */}
        <div className="bg-white p-6 rounded-lg shadow-md mb-8">
          <h2 className="text-xl font-semibold mb-4">Создать новую VNC сессию</h2>
          <div className="flex gap-4 items-end">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Display ID
              </label>
              <input
                type="number"
                min="1"
                max="99"
                value={newSession.display_id}
                onChange={(e) => setNewSession({...newSession, display_id: parseInt(e.target.value)})}
                className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Разрешение
              </label>
              <select
                value={newSession.geometry}
                onChange={(e) => setNewSession({...newSession, geometry: e.target.value})}
                className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="1024x768">1024x768</option>
                <option value="1280x720">1280x720</option>
                <option value="1280x1024">1280x1024</option>
                <option value="1440x900">1440x900</option>
                <option value="1920x1080">1920x1080</option>
              </select>
            </div>
            <button
              onClick={createSession}
              disabled={loading}
              className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? "Создание..." : "🚀 Создать сессию"}
            </button>
          </div>
        </div>

        {/* Sessions List */}
        <div className="bg-white p-6 rounded-lg shadow-md">
          <h2 className="text-xl font-semibold mb-4">Активные VNC сессии</h2>
          {sessions.length === 0 ? (
            <p className="text-gray-500 text-center py-8">Нет активных VNC сессий</p>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {sessions.map((session) => (
                <div key={session.id} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="font-semibold">Display :{session.display_id}</h3>
                    <span className={`px-2 py-1 rounded text-xs ${
                      session.status === 'active' 
                        ? 'bg-green-100 text-green-800' 
                        : 'bg-red-100 text-red-800'
                    }`}>
                      {session.status}
                    </span>
                  </div>
                  <div className="text-sm text-gray-600 mb-3">
                    <p>Port: {session.port}</p>
                    <p>WebSocket: {session.websocket_port}</p>
                    <p>Created: {new Date(session.created_at).toLocaleString()}</p>
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => getConnectionInfo(session.id)}
                      className="flex-1 px-3 py-1 bg-green-600 text-white rounded text-sm hover:bg-green-700"
                    >
                      🔗 Подключиться
                    </button>
                    <button
                      onClick={() => deleteSession(session.id)}
                      className="px-3 py-1 bg-red-600 text-white rounded text-sm hover:bg-red-700"
                    >
                      🗑️
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
        
        <div className="mt-8 bg-blue-50 p-6 rounded-lg">
          <h3 className="text-lg font-semibold text-blue-800 mb-2">ℹ️ Информация о VNC</h3>
          <ul className="text-blue-700 space-y-1">
            <li>• VNC (Virtual Network Computing) позволяет удаленно управлять рабочим столом</li>
            <li>• Каждая сессия запускается на отдельном дисплее с уникальным портом</li>
            <li>• Используйте кнопку "Подключиться" для получения ссылки на веб-клиент noVNC</li>
            <li>• Пароль для подключения: <code className="bg-blue-200 px-1 rounded">vncpass</code></li>
          </ul>
        </div>
      </div>
    </div>
  );
};

const Home = () => {
  const helloWorldApi = async () => {
    try {
      const response = await axios.get(`${API}/`);
      console.log(response.data.message);
    } catch (e) {
      console.error(e, `errored out requesting / api`);
    }
  };

  useEffect(() => {
    helloWorldApi();
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-900 to-purple-900">
      <div className="container mx-auto px-4 py-16">
        <div className="text-center text-white">
          <h1 className="text-5xl font-bold mb-6">🖥️ VNC Remote Desktop</h1>
          <p className="text-xl mb-8">Управляйте удаленными рабочими столами через веб-браузер</p>
          
          <div className="flex justify-center space-x-4">
            <Link 
              to="/vnc" 
              className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-6 rounded-lg text-lg transition duration-300"
            >
              🚀 Открыть VNC Manager
            </Link>
          </div>
        </div>
        
        <div className="mt-16 grid grid-cols-1 md:grid-cols-3 gap-8 text-white">
          <div className="bg-white bg-opacity-10 p-6 rounded-lg backdrop-blur-sm">
            <h3 className="text-xl font-semibold mb-3">🌐 Веб-доступ</h3>
            <p>Подключайтесь к удаленным рабочим столам прямо из браузера без установки дополнительного ПО</p>
          </div>
          
          <div className="bg-white bg-opacity-10 p-6 rounded-lg backdrop-blur-sm">
            <h3 className="text-xl font-semibold mb-3">⚡ Быстрое развертывание</h3>
            <p>Создавайте новые VNC сессии за секунды с настраиваемым разрешением экрана</p>
          </div>
          
          <div className="bg-white bg-opacity-10 p-6 rounded-lg backdrop-blur-sm">
            <h3 className="text-xl font-semibold mb-3">🔒 Безопасность</h3>
            <p>Все соединения защищены паролем, полная изоляция сессий</p>
          </div>
        </div>
      </div>
    </div>
  );
};

function App() {
  return (
    <div className="App">
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/vnc" element={<VNCManager />} />
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;