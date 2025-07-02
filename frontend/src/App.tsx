import React, { useState, useEffect } from 'react'
import './App.css'
import { Pie, Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend,
  CategoryScale,
  LinearScale,
  BarElement,
} from 'chart.js';
ChartJS.register(ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement);

function App() {
  const [file, setFile] = useState<File | null>(null)
  const [health, setHealth] = useState<string>('')
  const [uploadResult, setUploadResult] = useState<string>('')
  const [files, setFiles] = useState<any[]>([])
  const [summary, setSummary] = useState<any>(null)
  const [anomalies, setAnomalies] = useState<number[]>([])
  const [policyClusters, setPolicyClusters] = useState<string[][]>([])
  const [enriched, setEnriched] = useState<{ [key: string]: any[] }>({});
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [token, setToken] = useState('');
  const [userInfo, setUserInfo] = useState<any>(null);
  const [authMode, setAuthMode] = useState<'login' | 'register'>('login');
  const [comments, setComments] = useState<{ [key: number]: any[] }>({});
  const [commentInputs, setCommentInputs] = useState<{ [key: number]: string }>({});

  const checkHealth = async () => {
    const res = await fetch('http://localhost:8000/health')
    const data = await res.json()
    setHealth(data.status)
  }

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0])
    }
  }

  const handleUpload = async () => {
    if (!file) return
    const formData = new FormData()
    formData.append('file', file)
    const res = await fetch('http://localhost:8000/upload', {
      method: 'POST',
      body: formData,
    })
    const data = await res.json()
    setUploadResult(JSON.stringify(data))
  }

  const enrichPolicy = async (policy: string) => {
    const res = await fetch(`http://localhost:8000/enrich/topic?q=${encodeURIComponent(policy)}`);
    const data = await res.json();
    setEnriched((prev) => ({ ...prev, [policy]: data.results || [] }));
  };

  const handleAuth = async () => {
    const form = new FormData();
    form.append('username', username);
    form.append('password', password);
    const url = authMode === 'login' ? 'login' : 'register';
    const res = await fetch(`http://localhost:8000/${url}`, {
      method: 'POST',
      body: form,
    });
    const data = await res.json();
    if (authMode === 'login' && data.access_token) {
      setToken(data.access_token);
      // Fetch user info
      const me = await fetch('http://localhost:8000/me', {
        headers: { Authorization: `Bearer ${data.access_token}` },
      });
      setUserInfo(await me.json());
    } else if (authMode === 'register' && data.msg) {
      alert('Registration successful! Please log in.');
      setAuthMode('login');
    } else {
      alert(data.detail || 'Auth failed');
    }
  };

  const fetchComments = async (fileId: number) => {
    const res = await fetch(`http://localhost:8000/comments/${fileId}`);
    const data = await res.json();
    setComments((prev) => ({ ...prev, [fileId]: data }));
  };

  const addComment = async (fileId: number) => {
    if (!token) return alert('Login required');
    const content = commentInputs[fileId] || '';
    if (!content.trim()) return;
    const res = await fetch('http://localhost:8000/comment', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({ file_id: fileId.toString(), content }),
    });
    const data = await res.json();
    if (data.msg) {
      setCommentInputs((prev) => ({ ...prev, [fileId]: '' }));
      fetchComments(fileId);
    } else {
      alert(data.detail || 'Failed to add comment');
    }
  };

  useEffect(() => {
    fetch('http://localhost:8000/files')
      .then(res => res.json())
      .then(data => setFiles(data))
    fetch('http://localhost:8000/analytics/summary')
      .then(res => res.json())
      .then(data => setSummary(data))
    fetch('http://localhost:8000/analytics/anomalies')
      .then(res => res.json())
      .then(data => setAnomalies(data.anomalies))
    fetch('http://localhost:8000/analytics/policies')
      .then(res => res.json())
      .then(data => setPolicyClusters(data.clusters))
  }, [uploadResult])

  return (
    <div style={{ padding: 32 }}>
      <h1>Data-Driven Policy Dashboard</h1>
      <button onClick={checkHealth}>Check Backend Health</button>
      <div>Status: {health}</div>
      <hr />
      <input type="file" onChange={handleFileChange} />
      <button onClick={handleUpload} disabled={!file}>Upload</button>
      <div>Upload Result: {uploadResult}</div>
      <hr />
      <h2>Uploaded Files</h2>
      <table border="1" cellPadding={8}>
        <thead>
          <tr>
            <th>Filename</th>
            <th>File</th>
            <th>Summary</th>
            <th>Policies</th>
            <th>Comments</th>
          </tr>
        </thead>
        <tbody>
          {files.map(f => (
            <tr key={f.id}>
              <td>{f.filename}</td>
              <td>
                {f.file_url ? (
                  <a href={f.file_url.replace('s3://', 'https://s3.amazonaws.com/').replace('local://', '/')} target="_blank" rel="noopener noreferrer">View/Download</a>
                ) : 'N/A'}
              </td>
              <td>{f.summary}</td>
              <td>
                <ul>
                  {f.policies.map((p: string, i: number) => (
                    <li key={f.id + '-' + i + '-' + p}>
                      {p}
                      <button style={{ marginLeft: 8 }} onClick={() => enrichPolicy(p)}>Enrich</button>
                      {enriched[p] && (
                        <ul>
                          {enriched[p].map((r, j) => (
                            <li key={f.id + '-' + i + '-' + j + '-' + r.url}>
                              <a href={r.url} target="_blank" rel="noopener noreferrer">{r.name}</a>: {r.snippet}
                            </li>
                          ))}
                        </ul>
                      )}
                    </li>
                  ))}
                </ul>
              </td>
              <td colSpan={3}>
                <button onClick={() => fetchComments(f.id)}>Show Comments</button>
                <div>
                  {(comments[f.id] || []).map((c, i) => (
                    <div key={i} style={{ borderBottom: '1px solid #ccc', marginBottom: 4 }}>
                      <b>{c.user}</b> ({new Date(c.timestamp).toLocaleString()}): {c.content}
                      {c.policy_text && <div><i>Policy: {c.policy_text}</i></div>}
                    </div>
                  ))}
                  {token && (
                    <div>
                      <input
                        placeholder="Add a comment..."
                        value={commentInputs[f.id] || ''}
                        onChange={e => setCommentInputs(prev => ({ ...prev, [f.id]: e.target.value }))}
                      />
                      <button onClick={() => addComment(f.id)}>Add</button>
                    </div>
                  )}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <hr />
      <h2>Analytics</h2>
      {summary && (
        <div>
          <div>Total Files: {summary.total_files}</div>
          <div>Total Policies: {summary.total_policies}</div>
          <div>File Types: {Object.entries(summary.file_types).map(([k, v]) => `${k}: ${v}`).join(', ')}</div>
        </div>
      )}
      <div>
        <b>Anomalous File IDs:</b> {anomalies.join(', ')}
      </div>
      <div>
        <b>Policy Clusters:</b>
        <ol>
          {policyClusters.map((cluster, i) => (
            <li key={i}>
              <ul>
                {cluster.map((p, j) => <li key={`cluster${i}-policy${j}`}>{p}</li>)}
              </ul>
            </li>
          ))}
        </ol>
      </div>
      <hr />
      <h2>Visualizations</h2>
      {summary && (
        <div style={{ maxWidth: 400 }}>
          <h3>File Type Distribution</h3>
          <Pie
            data={{
              labels: Object.keys(summary.file_types),
              datasets: [
                {
                  data: Object.values(summary.file_types).map(Number),
                  backgroundColor: [
                    '#36A2EB', '#FF6384', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40',
                  ],
                },
              ],
            }}
          />
        </div>
      )}
      {policyClusters.length > 0 && (
        <div style={{ maxWidth: 400 }}>
          <h3>Policy Cluster Sizes</h3>
          <Bar
            data={{
              labels: policyClusters.map((_, i) => `Cluster ${i + 1}`),
              datasets: [
                {
                  label: 'Policies',
                  data: policyClusters.map((c) => c.length),
                  backgroundColor: '#36A2EB',
                },
              ],
            }}
            options={{
              indexAxis: 'y' as const,
              plugins: { legend: { display: false } },
              scales: { x: { beginAtZero: true } },
            }}
          />
        </div>
      )}
      <div style={{ marginBottom: 24 }}>
        {token ? (
          <div>
            <b>Logged in as:</b> {userInfo?.username} ({userInfo?.role})
            <button style={{ marginLeft: 8 }} onClick={() => { setToken(''); setUserInfo(null); }}>Logout</button>
          </div>
        ) : (
          <div>
            <input placeholder="Username" value={username} onChange={e => setUsername(e.target.value)} />
            <input placeholder="Password" type="password" value={password} onChange={e => setPassword(e.target.value)} />
            <button onClick={handleAuth}>{authMode === 'login' ? 'Login' : 'Register'}</button>
            <button onClick={() => setAuthMode(authMode === 'login' ? 'register' : 'login')}>
              {authMode === 'login' ? 'Switch to Register' : 'Switch to Login'}
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

export default App
