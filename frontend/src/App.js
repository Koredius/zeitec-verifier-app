import React, { useState, useEffect } from 'react';
import './App.css';

// API base URL
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

function App() {
  const [view, setView] = useState('home'); // home, login, registrant-apply, registrant-status, admin-dashboard
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));

  useEffect(() => {
    // Check if user is logged in
    if (token) {
      fetchCurrentUser();
    }
  }, [token]);

  const fetchCurrentUser = async () => {
    try {
      const response = await fetch(`${API_URL}/auth/me`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setUser(data.user);
      } else {
        localStorage.removeItem('token');
        setToken(null);
      }
    } catch (error) {
      console.error('Error fetching user:', error);
    }
  };

  const handleLogin = async (username, password) => {
    try {
      const response = await fetch(`${API_URL}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      });

      if (response.ok) {
        const data = await response.json();
        localStorage.setItem('token', data.access_token);
        setToken(data.access_token);
        setUser(data.user);
        setView('admin-dashboard');
        return { success: true };
      } else {
        const error = await response.json();
        return { success: false, error: error.error };
      }
    } catch (error) {
      return { success: false, error: 'Network error' };
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
    setView('home');
  };

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Navigation */}
      <nav className="bg-blue-600 text-white p-4 shadow-lg">
        <div className="container mx-auto flex justify-between items-center">
          <h1 className="text-2xl font-bold cursor-pointer" onClick={() => setView('home')}>
            Zeitec Verifier System
          </h1>
          <div className="space-x-4">
            {!user ? (
              <>
                <button onClick={() => setView('registrant-apply')} className="hover:underline">
                  Apply as Registrant
                </button>
                <button onClick={() => setView('registrant-status')} className="hover:underline">
                  Check Status
                </button>
                <button onClick={() => setView('login')} className="hover:underline">
                  Admin Login
                </button>
              </>
            ) : (
              <>
                <span>Welcome, {user.full_name || user.username}</span>
                <button onClick={handleLogout} className="hover:underline">
                  Logout
                </button>
              </>
            )}
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <div className="container mx-auto p-4">
        {view === 'home' && <HomeView setView={setView} />}
        {view === 'login' && <LoginView onLogin={handleLogin} setView={setView} />}
        {view === 'registrant-apply' && <RegistrantApplyView setView={setView} />}
        {view === 'registrant-status' && <RegistrantStatusView />}
        {view === 'admin-dashboard' && user && <AdminDashboard token={token} setView={setView} />}
      </div>
    </div>
  );
}

// Home View
function HomeView({ setView }) {
  return (
    <div className="max-w-4xl mx-auto text-center py-12">
      <h2 className="text-4xl font-bold mb-6">Welcome to Zeitec Verifier System</h2>
      <p className="text-xl mb-8 text-gray-700">
        Data verification platform for I-REC(E) certificates for small-scale renewable energy facilities
      </p>
      <div className="grid md:grid-cols-3 gap-6 mt-12">
        <div className="bg-white p-6 rounded-lg shadow-md hover:shadow-lg transition">
          <h3 className="text-xl font-bold mb-4">Phase 1</h3>
          <p className="text-gray-600 mb-4">Registrant Management</p>
          <button 
            onClick={() => setView('registrant-apply')}
            className="bg-blue-600 text-white px-6 py-2 rounded hover:bg-blue-700"
          >
            Apply Now
          </button>
        </div>
        <div className="bg-white p-6 rounded-lg shadow-md hover:shadow-lg transition">
          <h3 className="text-xl font-bold mb-4">Phase 2</h3>
          <p className="text-gray-600 mb-4">Device Registration</p>
          <button 
            className="bg-gray-400 text-white px-6 py-2 rounded cursor-not-allowed"
            disabled
          >
            Coming Soon
          </button>
        </div>
        <div className="bg-white p-6 rounded-lg shadow-md hover:shadow-lg transition">
          <h3 className="text-xl font-bold mb-4">Phase 3</h3>
          <p className="text-gray-600 mb-4">Issuance & Verification</p>
          <button 
            className="bg-gray-400 text-white px-6 py-2 rounded cursor-not-allowed"
            disabled
          >
            Coming Soon
          </button>
        </div>
      </div>
    </div>
  );
}

// Login View
function LoginView({ onLogin, setView }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    const result = await onLogin(username, password);

    if (!result.success) {
      setError(result.error);
    }

    setLoading(false);
  };

  return (
    <div className="max-w-md mx-auto mt-12">
      <div className="bg-white p-8 rounded-lg shadow-md">
        <h2 className="text-2xl font-bold mb-6">Admin Login</h2>
        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label className="block text-gray-700 mb-2">Username</label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full px-3 py-2 border rounded focus:outline-none focus:border-blue-500"
              required
            />
          </div>
          <div className="mb-6">
            <label className="block text-gray-700 mb-2">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-3 py-2 border rounded focus:outline-none focus:border-blue-500"
              required
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700 disabled:bg-gray-400"
          >
            {loading ? 'Logging in...' : 'Login'}
          </button>
        </form>
        <p className="mt-4 text-sm text-gray-600 text-center">
          Default credentials: admin / admin123
        </p>
      </div>
    </div>
  );
}

// Registrant Apply View
function RegistrantApplyView({ setView }) {
  const [formData, setFormData] = useState({
    organization_name: '',
    contact_person: '',
    email: '',
    phone: '',
    country: 'Nigeria',
    num_facilities: '',
    total_capacity_kw: '',
    description: ''
  });
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    const formDataToSend = new FormData();
    Object.keys(formData).forEach(key => {
      if (formData[key]) formDataToSend.append(key, formData[key]);
    });
    if (file) formDataToSend.append('business_document', file);

    try {
      const response = await fetch(`${API_URL}/registrants/apply`, {
        method: 'POST',
        body: formDataToSend
      });

      if (response.ok) {
        setSuccess(true);
      } else {
        const data = await response.json();
        setError(data.error || 'Application failed');
      }
    } catch (error) {
      setError('Network error. Please try again.');
    }

    setLoading(false);
  };

  if (success) {
    return (
      <div className="max-w-2xl mx-auto mt-12">
        <div className="bg-green-100 border border-green-400 text-green-700 px-6 py-4 rounded-lg">
          <h3 className="text-xl font-bold mb-2">✅ Application Submitted Successfully!</h3>
          <p className="mb-4">
            Your application has been received. You can check your status using your email address.
          </p>
          <button
            onClick={() => setView('registrant-status')}
            className="bg-green-600 text-white px-6 py-2 rounded hover:bg-green-700"
          >
            Check Status
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto mt-8">
      <div className="bg-white p-8 rounded-lg shadow-md">
        <h2 className="text-2xl font-bold mb-6">Registrant Application</h2>
        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}
        <form onSubmit={handleSubmit}>
          <div className="grid md:grid-cols-2 gap-4">
            <div className="mb-4">
              <label className="block text-gray-700 mb-2">Organization Name *</label>
              <input
                type="text"
                value={formData.organization_name}
                onChange={(e) => setFormData({...formData, organization_name: e.target.value})}
                className="w-full px-3 py-2 border rounded focus:outline-none focus:border-blue-500"
                required
              />
            </div>
            <div className="mb-4">
              <label className="block text-gray-700 mb-2">Contact Person *</label>
              <input
                type="text"
                value={formData.contact_person}
                onChange={(e) => setFormData({...formData, contact_person: e.target.value})}
                className="w-full px-3 py-2 border rounded focus:outline-none focus:border-blue-500"
                required
              />
            </div>
            <div className="mb-4">
              <label className="block text-gray-700 mb-2">Email *</label>
              <input
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({...formData, email: e.target.value})}
                className="w-full px-3 py-2 border rounded focus:outline-none focus:border-blue-500"
                required
              />
            </div>
            <div className="mb-4">
              <label className="block text-gray-700 mb-2">Phone</label>
              <input
                type="tel"
                value={formData.phone}
                onChange={(e) => setFormData({...formData, phone: e.target.value})}
                className="w-full px-3 py-2 border rounded focus:outline-none focus:border-blue-500"
              />
            </div>
            <div className="mb-4">
              <label className="block text-gray-700 mb-2">Country *</label>
              <select
                value={formData.country}
                onChange={(e) => setFormData({...formData, country: e.target.value})}
                className="w-full px-3 py-2 border rounded focus:outline-none focus:border-blue-500"
                required
              >
                <option value="Nigeria">Nigeria</option>
                <option value="Benin">Benin</option>
                <option value="Ghana">Ghana</option>
                <option value="Kenya">Kenya</option>
                <option value="South Africa">South Africa</option>
              </select>
            </div>
            <div className="mb-4">
              <label className="block text-gray-700 mb-2">Number of Facilities</label>
              <input
                type="number"
                value={formData.num_facilities}
                onChange={(e) => setFormData({...formData, num_facilities: e.target.value})}
                className="w-full px-3 py-2 border rounded focus:outline-none focus:border-blue-500"
              />
            </div>
            <div className="mb-4">
              <label className="block text-gray-700 mb-2">Total Capacity (kW)</label>
              <input
                type="number"
                step="0.01"
                value={formData.total_capacity_kw}
                onChange={(e) => setFormData({...formData, total_capacity_kw: e.target.value})}
                className="w-full px-3 py-2 border rounded focus:outline-none focus:border-blue-500"
              />
            </div>
          </div>
          <div className="mb-4">
            <label className="block text-gray-700 mb-2">Description</label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({...formData, description: e.target.value})}
              className="w-full px-3 py-2 border rounded focus:outline-none focus:border-blue-500"
              rows="3"
            ></textarea>
          </div>
          <div className="mb-6">
            <label className="block text-gray-700 mb-2">Business Registration Document</label>
            <input
              type="file"
              onChange={(e) => setFile(e.target.files[0])}
              className="w-full px-3 py-2 border rounded focus:outline-none focus:border-blue-500"
              accept=".pdf,.doc,.docx,.jpg,.jpeg,.png"
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 text-white py-3 rounded hover:bg-blue-700 disabled:bg-gray-400"
          >
            {loading ? 'Submitting...' : 'Submit Application'}
          </button>
        </form>
      </div>
    </div>
  );
}

// Registrant Status View
function RegistrantStatusView() {
  const [email, setEmail] = useState('');
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleCheck = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    setStatus(null);

    try {
      const response = await fetch(`${API_URL}/registrants/status/${encodeURIComponent(email)}`);

      if (response.ok) {
        const data = await response.json();
        setStatus(data);
      } else {
        const data = await response.json();
        setError(data.error || 'Status check failed');
      }
    } catch (error) {
      setError('Network error. Please try again.');
    }

    setLoading(false);
  };

  return (
    <div className="max-w-md mx-auto mt-12">
      <div className="bg-white p-8 rounded-lg shadow-md">
        <h2 className="text-2xl font-bold mb-6">Check Application Status</h2>
        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}
        <form onSubmit={handleCheck}>
          <div className="mb-4">
            <label className="block text-gray-700 mb-2">Email Address</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-3 py-2 border rounded focus:outline-none focus:border-blue-500"
              placeholder="Enter your email"
              required
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700 disabled:bg-gray-400"
          >
            {loading ? 'Checking...' : 'Check Status'}
          </button>
        </form>

        {status && (
          <div className="mt-6 p-4 bg-gray-50 rounded">
            <h3 className="font-bold mb-2">Application Status</h3>
            <p><strong>Organization:</strong> {status.organization_name}</p>
            <p><strong>Status:</strong> 
              <span className={`ml-2 px-2 py-1 rounded text-sm ${
                status.status === 'approved' ? 'bg-green-200 text-green-800' :
                status.status === 'rejected' ? 'bg-red-200 text-red-800' :
                'bg-yellow-200 text-yellow-800'
              }`}>
                {status.status.toUpperCase()}
              </span>
            </p>
            <p><strong>Submitted:</strong> {new Date(status.submitted_at).toLocaleDateString()}</p>
            {status.reviewed_at && (
              <p><strong>Reviewed:</strong> {new Date(status.reviewed_at).toLocaleDateString()}</p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

// Admin Dashboard (simplified - shows all 3 phases)
function AdminDashboard({ token, setView }) {
  const [activeTab, setActiveTab] = useState('registrants');
  const [registrants, setRegistrants] = useState([]);
  const [devices, setDevices] = useState([]);
  const [submissions, setSubmissions] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (activeTab === 'registrants') fetchRegistrants();
    if (activeTab === 'devices') fetchDevices();
    if (activeTab === 'issuance') fetchSubmissions();
  }, [activeTab]);

  const fetchRegistrants = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/registrants/?status=pending`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setRegistrants(data.registrants);
      }
    } catch (error) {
      console.error('Error fetching registrants:', error);
    }
    setLoading(false);
  };

  const fetchDevices = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/devices/?status=pending`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setDevices(data.devices);
      }
    } catch (error) {
      console.error('Error fetching devices:', error);
    }
    setLoading(false);
  };

  const fetchSubmissions = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/issuance/?status=pending`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setSubmissions(data.submissions);
      }
    } catch (error) {
      console.error('Error fetching submissions:', error);
    }
    setLoading(false);
  };

  const handleApproveRegistrant = async (id) => {
    try {
      const response = await fetch(`${API_URL}/registrants/${id}/approve`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ notes: 'Approved via dashboard' })
      });
      if (response.ok) {
        fetchRegistrants();
        alert('Registrant approved successfully!');
      }
    } catch (error) {
      alert('Error approving registrant');
    }
  };

  const handleRejectRegistrant = async (id) => {
    const notes = prompt('Enter rejection reason:');
    if (!notes) return;

    try {
      const response = await fetch(`${API_URL}/registrants/${id}/reject`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ notes })
      });
      if (response.ok) {
        fetchRegistrants();
        alert('Registrant rejected');
      }
    } catch (error) {
      alert('Error rejecting registrant');
    }
  };

  return (
    <div className="mt-8">
      <h2 className="text-3xl font-bold mb-6">Admin Dashboard</h2>

      {/* Tabs */}
      <div className="flex space-x-4 mb-6 border-b">
        <button
          onClick={() => setActiveTab('registrants')}
          className={`pb-2 px-4 ${activeTab === 'registrants' ? 'border-b-2 border-blue-600 font-bold' : ''}`}
        >
          Phase 1: Registrants
        </button>
        <button
          onClick={() => setActiveTab('devices')}
          className={`pb-2 px-4 ${activeTab === 'devices' ? 'border-b-2 border-blue-600 font-bold' : ''}`}
        >
          Phase 2: Devices
        </button>
        <button
          onClick={() => setActiveTab('issuance')}
          className={`pb-2 px-4 ${activeTab === 'issuance' ? 'border-b-2 border-blue-600 font-bold' : ''}`}
        >
          Phase 3: Issuance
        </button>
      </div>

      {/* Registrants Tab */}
      {activeTab === 'registrants' && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-xl font-bold mb-4">Pending Registrant Applications</h3>
          {loading ? (
            <p>Loading...</p>
          ) : registrants.length === 0 ? (
            <p className="text-gray-600">No pending applications</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="bg-gray-100">
                    <th className="p-2 text-left">Organization</th>
                    <th className="p-2 text-left">Contact</th>
                    <th className="p-2 text-left">Country</th>
                    <th className="p-2 text-left">Facilities</th>
                    <th className="p-2 text-left">Submitted</th>
                    <th className="p-2 text-left">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {registrants.map(reg => (
                    <tr key={reg.id} className="border-b">
                      <td className="p-2">{reg.organization_name}</td>
                      <td className="p-2">{reg.contact_person}<br/><small>{reg.email}</small></td>
                      <td className="p-2">{reg.country}</td>
                      <td className="p-2">{reg.num_facilities || 'N/A'}</td>
                      <td className="p-2">{new Date(reg.created_at).toLocaleDateString()}</td>
                      <td className="p-2">
                        <button
                          onClick={() => handleApproveRegistrant(reg.id)}
                          className="bg-green-600 text-white px-3 py-1 rounded mr-2 hover:bg-green-700"
                        >
                          Approve
                        </button>
                        <button
                          onClick={() => handleRejectRegistrant(reg.id)}
                          className="bg-red-600 text-white px-3 py-1 rounded hover:bg-red-700"
                        >
                          Reject
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Devices Tab */}
      {activeTab === 'devices' && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-xl font-bold mb-4">Pending Device Registrations</h3>
          {loading ? (
            <p>Loading...</p>
          ) : devices.length === 0 ? (
            <p className="text-gray-600">No pending devices</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="bg-gray-100">
                    <th className="p-2 text-left">Device ID</th>
                    <th className="p-2 text-left">Facility ID</th>
                    <th className="p-2 text-left">Registrant</th>
                    <th className="p-2 text-left">Capacity (kW)</th>
                    <th className="p-2 text-left">Country</th>
                    <th className="p-2 text-left">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {devices.map(device => (
                    <tr key={device.id} className="border-b">
                      <td className="p-2">{device.device_id}</td>
                      <td className="p-2">{device.facility_id}</td>
                      <td className="p-2">{device.registrant_name}</td>
                      <td className="p-2">{device.capacity_kw}</td>
                      <td className="p-2">{device.country}</td>
                      <td className="p-2">
                        <button className="bg-blue-600 text-white px-3 py-1 rounded hover:bg-blue-700">
                          Review
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* Issuance Tab */}
      {activeTab === 'issuance' && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-xl font-bold mb-4">Pending Issuance Submissions</h3>
          {loading ? (
            <p>Loading...</p>
          ) : submissions.length === 0 ? (
            <p className="text-gray-600">No pending submissions</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="bg-gray-100">
                    <th className="p-2 text-left">ID</th>
                    <th className="p-2 text-left">Registrant</th>
                    <th className="p-2 text-left">Device</th>
                    <th className="p-2 text-left">Total kWh</th>
                    <th className="p-2 text-left">Period</th>
                    <th className="p-2 text-left">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {submissions.map(sub => (
                    <tr key={sub.id} className="border-b">
                      <td className="p-2">{sub.id}</td>
                      <td className="p-2">{sub.registrant_name}</td>
                      <td className="p-2">{sub.device_info}</td>
                      <td className="p-2">{sub.total_kwh?.toFixed(2)}</td>
                      <td className="p-2">
                        {new Date(sub.issuance_period_start).toLocaleDateString()} -<br/>
                        {new Date(sub.issuance_period_end).toLocaleDateString()}
                      </td>
                      <td className="p-2">
                        <button className="bg-blue-600 text-white px-3 py-1 rounded hover:bg-blue-700">
                          Review
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default App;
