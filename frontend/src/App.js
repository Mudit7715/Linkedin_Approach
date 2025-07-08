import React, { useState, useEffect } from "react";
import "./App.css";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Dashboard = () => {
  const [activeTab, setActiveTab] = useState("overview");
  const [analytics, setAnalytics] = useState(null);
  const [targets, setTargets] = useState([]);
  const [messages, setMessages] = useState([]);
  const [viralPosts, setViralPosts] = useState([]);
  const [generatedPosts, setGeneratedPosts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [newTarget, setNewTarget] = useState({
    name: "",
    title: "",
    company: "",
    linkedin_url: "",
    email: "",
    phone: "",
    profile_summary: "",
    recent_activity: ""
  });
  const [messageGeneration, setMessageGeneration] = useState({
    target_id: "",
    message_type: "connection_request",
    llm_provider: "openai"
  });

  useEffect(() => {
    fetchAnalytics();
    fetchTargets();
    fetchMessages();
    fetchViralPosts();
    fetchGeneratedPosts();
  }, []);

  const fetchAnalytics = async () => {
    try {
      const response = await axios.get(`${API}/analytics`);
      setAnalytics(response.data);
    } catch (error) {
      console.error("Error fetching analytics:", error);
    }
  };

  const fetchTargets = async () => {
    try {
      const response = await axios.get(`${API}/targets`);
      setTargets(response.data);
    } catch (error) {
      console.error("Error fetching targets:", error);
    }
  };

  const fetchMessages = async () => {
    try {
      const response = await axios.get(`${API}/messages`);
      setMessages(response.data);
    } catch (error) {
      console.error("Error fetching messages:", error);
    }
  };

  const fetchViralPosts = async () => {
    try {
      const response = await axios.get(`${API}/viral-posts`);
      setViralPosts(response.data);
    } catch (error) {
      console.error("Error fetching viral posts:", error);
    }
  };

  const fetchGeneratedPosts = async () => {
    try {
      const response = await axios.get(`${API}/generated-posts`);
      setGeneratedPosts(response.data);
    } catch (error) {
      console.error("Error fetching generated posts:", error);
    }
  };

  const createTarget = async () => {
    try {
      setLoading(true);
      await axios.post(`${API}/targets`, newTarget);
      setNewTarget({
        name: "",
        title: "",
        company: "",
        linkedin_url: "",
        email: "",
        phone: "",
        profile_summary: "",
        recent_activity: ""
      });
      fetchTargets();
    } catch (error) {
      console.error("Error creating target:", error);
    } finally {
      setLoading(false);
    }
  };

  const generateMessage = async (targetId) => {
    try {
      setLoading(true);
      const target = targets.find(t => t.id === targetId);
      if (!target) return;

      const response = await axios.post(`${API}/messages/generate`, {
        target_id: targetId,
        profile_data: {
          name: target.name,
          title: target.title,
          company: target.company,
          profile_summary: target.profile_summary,
          recent_activity: target.recent_activity
        },
        message_type: messageGeneration.message_type,
        llm_provider: messageGeneration.llm_provider
      });

      fetchMessages();
      alert("Message generated successfully!");
    } catch (error) {
      console.error("Error generating message:", error);
      alert("Error generating message: " + error.response?.data?.detail || error.message);
    } finally {
      setLoading(false);
    }
  };

  const generateViralPost = async () => {
    try {
      setLoading(true);
      await axios.post(`${API}/generate-post`);
      fetchGeneratedPosts();
      alert("Viral post generated successfully!");
    } catch (error) {
      console.error("Error generating post:", error);
      alert("Error generating post: " + error.response?.data?.detail || error.message);
    } finally {
      setLoading(false);
    }
  };

  const testConnections = async () => {
    try {
      const [openaiTest, ollamaTest] = await Promise.all([
        axios.get(`${API}/test/openai`),
        axios.get(`${API}/test/ollama`)
      ]);

      alert(`OpenAI: ${openaiTest.data.status}\nOllama: ${ollamaTest.data.status}`);
    } catch (error) {
      console.error("Error testing connections:", error);
      alert("Error testing connections");
    }
  };

  const TabButton = ({ id, label, active, onClick }) => (
    <button
      onClick={() => onClick(id)}
      className={`px-6 py-3 rounded-lg font-medium transition-all duration-200 ${
        active
          ? "bg-blue-600 text-white shadow-lg"
          : "bg-gray-100 text-gray-700 hover:bg-gray-200"
      }`}
    >
      {label}
    </button>
  );

  const StatCard = ({ title, value, change, color = "blue" }) => (
    <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-2xl font-bold text-gray-900">{value}</p>
        </div>
        <div className={`w-12 h-12 rounded-lg bg-${color}-100 flex items-center justify-center`}>
          <div className={`w-6 h-6 rounded-full bg-${color}-500`}></div>
        </div>
      </div>
      {change && (
        <p className="text-sm text-gray-500 mt-2">{change}</p>
      )}
    </div>
  );

  const OverviewTab = () => (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-gray-900">LinkedIn AI Automation Dashboard</h2>
        <button
          onClick={testConnections}
          className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
        >
          Test Connections
        </button>
      </div>

      {analytics && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <StatCard
            title="Total Targets"
            value={analytics.total_targets}
            color="blue"
          />
          <StatCard
            title="Connections Sent"
            value={analytics.connections_sent}
            color="green"
          />
          <StatCard
            title="Acceptance Rate"
            value={`${analytics.acceptance_rate}%`}
            color="purple"
          />
          <StatCard
            title="Reply Rate"
            value={`${analytics.reply_rate}%`}
            color="orange"
          />
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Activity</h3>
          {analytics?.daily_activity && (
            <div className="space-y-2">
              {Object.entries(analytics.daily_activity).map(([date, count]) => (
                <div key={date} className="flex justify-between items-center">
                  <span className="text-sm text-gray-600">{date}</span>
                  <span className="text-sm font-medium text-gray-900">{count} actions</span>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
          <div className="space-y-3">
            <button
              onClick={() => setActiveTab("targets")}
              className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
            >
              Add New Target
            </button>
            <button
              onClick={() => setActiveTab("messages")}
              className="w-full px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
            >
              Generate Messages
            </button>
            <button
              onClick={() => setActiveTab("posts")}
              className="w-full px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700"
            >
              Create Viral Post
            </button>
          </div>
        </div>
      </div>
    </div>
  );

  const TargetsTab = () => (
    <div className="space-y-6">
      <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Add New Target</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <input
            type="text"
            placeholder="Name"
            value={newTarget.name}
            onChange={(e) => setNewTarget({...newTarget, name: e.target.value})}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          <input
            type="text"
            placeholder="Title"
            value={newTarget.title}
            onChange={(e) => setNewTarget({...newTarget, title: e.target.value})}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          <input
            type="text"
            placeholder="Company"
            value={newTarget.company}
            onChange={(e) => setNewTarget({...newTarget, company: e.target.value})}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          <input
            type="url"
            placeholder="LinkedIn URL"
            value={newTarget.linkedin_url}
            onChange={(e) => setNewTarget({...newTarget, linkedin_url: e.target.value})}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          <input
            type="email"
            placeholder="Email"
            value={newTarget.email}
            onChange={(e) => setNewTarget({...newTarget, email: e.target.value})}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          <input
            type="tel"
            placeholder="Phone"
            value={newTarget.phone}
            onChange={(e) => setNewTarget({...newTarget, phone: e.target.value})}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>
        <div className="mt-4 space-y-3">
          <textarea
            placeholder="Profile Summary"
            value={newTarget.profile_summary}
            onChange={(e) => setNewTarget({...newTarget, profile_summary: e.target.value})}
            rows="3"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          <textarea
            placeholder="Recent Activity"
            value={newTarget.recent_activity}
            onChange={(e) => setNewTarget({...newTarget, recent_activity: e.target.value})}
            rows="2"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
        </div>
        <button
          onClick={createTarget}
          disabled={loading}
          className="mt-4 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
        >
          {loading ? "Creating..." : "Add Target"}
        </button>
      </div>

      <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Existing Targets</h3>
        <div className="space-y-4">
          {targets.map((target) => (
            <div key={target.id} className="border border-gray-200 rounded-lg p-4">
              <div className="flex justify-between items-start">
                <div>
                  <h4 className="font-medium text-gray-900">{target.name}</h4>
                  <p className="text-sm text-gray-600">{target.title} at {target.company}</p>
                  <p className="text-sm text-gray-500">Status: {target.connection_status}</p>
                </div>
                <button
                  onClick={() => generateMessage(target.id)}
                  className="px-3 py-1 bg-green-600 text-white text-sm rounded hover:bg-green-700"
                >
                  Generate Message
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );

  const MessagesTab = () => (
    <div className="space-y-6">
      <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Message Generation Settings</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <select
            value={messageGeneration.message_type}
            onChange={(e) => setMessageGeneration({...messageGeneration, message_type: e.target.value})}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="connection_request">Connection Request</option>
            <option value="follow_up">Follow Up</option>
            <option value="viral_post">Viral Post</option>
          </select>
          <select
            value={messageGeneration.llm_provider}
            onChange={(e) => setMessageGeneration({...messageGeneration, llm_provider: e.target.value})}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="openai">OpenAI</option>
            <option value="ollama">Ollama</option>
          </select>
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Generated Messages</h3>
        <div className="space-y-4">
          {messages.map((message) => (
            <div key={message.id} className="border border-gray-200 rounded-lg p-4">
              <div className="flex justify-between items-start mb-2">
                <div>
                  <span className="text-sm font-medium text-gray-900">{message.message_type}</span>
                  <span className={`ml-2 px-2 py-1 text-xs rounded ${
                    message.status === 'sent' ? 'bg-green-100 text-green-800' :
                    message.status === 'draft' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-gray-100 text-gray-800'
                  }`}>
                    {message.status}
                  </span>
                </div>
                <span className="text-xs text-gray-500">
                  {new Date(message.created_at).toLocaleDateString()}
                </span>
              </div>
              <p className="text-sm text-gray-700 bg-gray-50 p-3 rounded">{message.content}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );

  const PostsTab = () => (
    <div className="space-y-6">
      <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Viral Post Generator</h3>
          <button
            onClick={generateViralPost}
            disabled={loading}
            className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50"
          >
            {loading ? "Generating..." : "Generate Post"}
          </button>
        </div>
        <p className="text-sm text-gray-600">Generate viral posts based on trending AI/ML content</p>
      </div>

      <div className="bg-white rounded-xl shadow-sm p-6 border border-gray-100">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Generated Posts</h3>
        <div className="space-y-4">
          {generatedPosts.map((post) => (
            <div key={post.id} className="border border-gray-200 rounded-lg p-4">
              <div className="flex justify-between items-start mb-2">
                <span className={`px-2 py-1 text-xs rounded ${
                  post.status === 'published' ? 'bg-green-100 text-green-800' :
                  post.status === 'approved' ? 'bg-blue-100 text-blue-800' :
                  'bg-yellow-100 text-yellow-800'
                }`}>
                  {post.status}
                </span>
                <span className="text-xs text-gray-500">
                  {new Date(post.created_at).toLocaleDateString()}
                </span>
              </div>
              <p className="text-sm text-gray-700 bg-gray-50 p-3 rounded whitespace-pre-wrap">{post.content}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">LinkedIn AI Automation</h1>
          <p className="text-gray-600">Automate your LinkedIn outreach with AI-powered personalization</p>
        </div>

        {/* Navigation */}
        <div className="flex flex-wrap gap-2 mb-8">
          <TabButton id="overview" label="Overview" active={activeTab === "overview"} onClick={setActiveTab} />
          <TabButton id="targets" label="Targets" active={activeTab === "targets"} onClick={setActiveTab} />
          <TabButton id="messages" label="Messages" active={activeTab === "messages"} onClick={setActiveTab} />
          <TabButton id="posts" label="Posts" active={activeTab === "posts"} onClick={setActiveTab} />
        </div>

        {/* Content */}
        {activeTab === "overview" && <OverviewTab />}
        {activeTab === "targets" && <TargetsTab />}
        {activeTab === "messages" && <MessagesTab />}
        {activeTab === "posts" && <PostsTab />}
      </div>
    </div>
  );
};

function App() {
  return (
    <div className="App">
      <Dashboard />
    </div>
  );
}

export default App;