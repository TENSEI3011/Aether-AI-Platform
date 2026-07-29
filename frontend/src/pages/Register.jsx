/**
 * Register Page — InsightAI split-layout with feature pills
 * Logic preserved: register() from AuthContext → navigate('/dashboard')
 */

import React, { useState, useEffect, useRef } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'

// Reuse the same WebGL shader from Login
function ShaderCanvas() {
    const canvasRef = useRef(null)

    useEffect(() => {
        const canvas = canvasRef.current
        if (!canvas) return

        const syncSize = () => {
            const w = canvas.clientWidth || 1280
            const h = canvas.clientHeight || 720
            if (canvas.width !== w || canvas.height !== h) {
                canvas.width = w; canvas.height = h
            }
        }
        const ro = typeof ResizeObserver !== 'undefined' ? new ResizeObserver(syncSize) : null
        ro?.observe(canvas); syncSize()

        const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl')
        if (!gl) return

        const vs = `attribute vec2 a_position;varying vec2 v_texCoord;void main(){v_texCoord=a_position*0.5+0.5;gl_Position=vec4(a_position,0.0,1.0);}`
        const fs = `precision highp float;varying vec2 v_texCoord;uniform float u_time;uniform vec2 u_resolution;uniform vec2 u_mouse;
float orb(vec2 uv,vec2 pos,float size,float intensity){float d=length(uv-pos);return pow(size/d,intensity);}
void main(){vec2 uv=v_texCoord;vec2 mouse=u_mouse/u_resolution;
vec3 color=vec3(0.059,0.059,0.102);
float t1=u_time*0.35;float t2=u_time*0.28;float t3=u_time*0.45;
vec2 p1=vec2(0.25+0.12*sin(t1),0.6+0.15*cos(t1));
vec2 p2=vec2(0.75+0.1*cos(t2),0.35+0.12*sin(t2));
vec2 p3=vec2(0.55+0.18*sin(t3),0.75+0.08*cos(t3));
vec2 p4=mouse;
vec3 accent=vec3(0.0,0.82,1.0);
vec3 purple=vec3(0.4235,0.3882,1.0);
float g1=orb(uv,p1,0.07,1.9);float g2=orb(uv,p2,0.09,1.7);
float g3=orb(uv,p3,0.05,2.1);float g4=orb(uv,p4,0.04,2.5)*0.25;
color+=purple*(g1+g3)+accent*(g2)+purple*(g4);
float v=1.0-length(uv-0.5)*1.15;color*=v;
gl_FragColor=vec4(color,1.0);}`

        const mkShader = (type, src) => {
            const s = gl.createShader(type)
            gl.shaderSource(s, src); gl.compileShader(s); return s
        }
        const prog = gl.createProgram()
        gl.attachShader(prog, mkShader(gl.VERTEX_SHADER, vs))
        gl.attachShader(prog, mkShader(gl.FRAGMENT_SHADER, fs))
        gl.linkProgram(prog); gl.useProgram(prog)

        const buf = gl.createBuffer()
        gl.bindBuffer(gl.ARRAY_BUFFER, buf)
        gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1,-1,1,-1,-1,1,1,1]), gl.STATIC_DRAW)
        const pos = gl.getAttribLocation(prog, 'a_position')
        gl.enableVertexAttribArray(pos)
        gl.vertexAttribPointer(pos, 2, gl.FLOAT, false, 0, 0)

        const uTime  = gl.getUniformLocation(prog, 'u_time')
        const uRes   = gl.getUniformLocation(prog, 'u_resolution')
        const uMouse = gl.getUniformLocation(prog, 'u_mouse')

        let mouse = { x: canvas.width / 2, y: canvas.height / 2 }
        const onMove = (e) => {
            const rect = canvas.getBoundingClientRect()
            if (rect.width && rect.height) {
                mouse.x = ((e.clientX - rect.left) / rect.width) * canvas.width
                mouse.y = (1 - (e.clientY - rect.top) / rect.height) * canvas.height
            }
        }
        window.addEventListener('mousemove', onMove)

        let raf
        const render = (t) => {
            if (!ro) syncSize()
            gl.viewport(0, 0, canvas.width, canvas.height)
            if (uTime)  gl.uniform1f(uTime, t * 0.001)
            if (uRes)   gl.uniform2f(uRes, canvas.width, canvas.height)
            if (uMouse) gl.uniform2f(uMouse, mouse.x, mouse.y)
            gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4)
            raf = requestAnimationFrame(render)
        }
        raf = requestAnimationFrame(render)

        return () => {
            cancelAnimationFrame(raf)
            window.removeEventListener('mousemove', onMove)
            ro?.disconnect()
        }
    }, [])

    return <canvas ref={canvasRef} className="shader-canvas" />
}

const FEATURES = [
    { icon: '💬', label: 'Natural Language Queries' },
    { icon: '📊', label: 'AI-Powered Charts' },
    { icon: '🎙️', label: 'Voice Input' },
]

function Register() {
    const [username, setUsername] = useState('')
    const [email, setEmail]       = useState('')
    const [password, setPassword] = useState('')
    const [error, setError]       = useState('')
    const [loading, setLoading]   = useState(false)
    const { register } = useAuth()
    const navigate = useNavigate()

    const handleSubmit = async (e) => {
        e.preventDefault()
        setError(''); setLoading(true)
        try {
            await register(username, email, password)
            navigate('/dashboard')
        } catch (err) {
            setError(err.response?.data?.detail || 'Registration failed. Try a different username.')
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="auth-page">
            {/* ── Left: Hero ── */}
            <div className="auth-hero">
                <ShaderCanvas />
                <div className="auth-hero-gradient-b" />
                <div className="auth-hero-gradient-l" />
                <div className="auth-hero-content">
                    <h1 className="auth-hero-title">
                        Start Your<br />Data Journey
                    </h1>
                    <p className="auth-hero-subtitle">
                        Create a free account and begin analyzing your data with AI in minutes.
                    </p>
                    <div className="feature-pills">
                        {FEATURES.map(f => (
                            <span key={f.label} className="feature-pill">
                                {f.icon} {f.label}
                            </span>
                        ))}
                    </div>
                </div>
            </div>

            {/* ── Right: Register Form ── */}
            <div className="auth-form-panel">
                <div className="glass-panel auth-card">
                    <div className="auth-logo-row">
                        <div className="auth-logo-icon">✦</div>
                        <div className="auth-logo-name">InsightAI</div>
                    </div>

                    {error && (
                        <div className="alert alert-error" style={{ marginBottom: '1.25rem' }}>
                            ⚠ {error}
                        </div>
                    )}

                    <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                        <div className="input-group" style={{ marginBottom: 0 }}>
                            <label htmlFor="reg-username">Username</label>
                            <input
                                id="reg-username"
                                className="input-field"
                                type="text"
                                value={username}
                                onChange={(e) => setUsername(e.target.value)}
                                placeholder="Choose a username"
                                required
                                autoComplete="username"
                            />
                        </div>
                        <div className="input-group" style={{ marginBottom: 0 }}>
                            <label htmlFor="reg-email">Email</label>
                            <input
                                id="reg-email"
                                className="input-field"
                                type="email"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                placeholder="name@company.com"
                                required
                                autoComplete="email"
                            />
                        </div>
                        <div className="input-group" style={{ marginBottom: 0 }}>
                            <label htmlFor="reg-password">Password</label>
                            <input
                                id="reg-password"
                                className="input-field"
                                type="password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                placeholder="Min 6 characters"
                                required
                                minLength={6}
                                autoComplete="new-password"
                            />
                        </div>
                        <button
                            className="btn btn-primary"
                            type="submit"
                            disabled={loading}
                            style={{ width: '100%', marginTop: '0.5rem', padding: '0.8rem' }}
                        >
                            {loading ? (
                                <><div className="spinner" style={{ width: 18, height: 18 }} /> Creating Account...</>
                            ) : (
                                'Create Account →'
                            )}
                        </button>
                    </form>

                    <div className="auth-footer">
                        Already have an account? <Link to="/login">Sign In</Link>
                    </div>
                </div>
            </div>
        </div>
    )
}

export default Register
