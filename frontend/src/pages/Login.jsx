/**
 * Login Page — Aether AI split-layout with WebGL shader hero
 * Logic preserved: login() from AuthContext → navigate('/dashboard')
 */

import React, { useState, useEffect, useRef } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'

// WebGL shader: pulsing purple orbs reactive to mouse
function ShaderCanvas() {
    const canvasRef = useRef(null)

    useEffect(() => {
        const canvas = canvasRef.current
        if (!canvas) return

        const syncSize = () => {
            const w = canvas.clientWidth || 1280
            const h = canvas.clientHeight || 720
            if (canvas.width !== w || canvas.height !== h) {
                canvas.width = w
                canvas.height = h
            }
        }

        const ro = typeof ResizeObserver !== 'undefined'
            ? new ResizeObserver(syncSize)
            : null
        ro?.observe(canvas)
        syncSize()

        const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl')
        if (!gl) return

        const vs = `attribute vec2 a_position;varying vec2 v_texCoord;void main(){v_texCoord=a_position*0.5+0.5;gl_Position=vec4(a_position,0.0,1.0);}`
        const fs = `precision highp float;varying vec2 v_texCoord;uniform float u_time;uniform vec2 u_resolution;uniform vec2 u_mouse;
float orb(vec2 uv,vec2 pos,float size,float intensity){float d=length(uv-pos);return pow(size/d,intensity);}
void main(){vec2 uv=v_texCoord;vec2 mouse=u_mouse/u_resolution;
vec3 color=vec3(0.059,0.059,0.102);
float t1=u_time*0.4;float t2=u_time*0.3;float t3=u_time*0.5;
vec2 p1=vec2(0.3+0.1*sin(t1),0.5+0.2*cos(t1));
vec2 p2=vec2(0.7+0.15*cos(t2),0.4+0.1*sin(t2));
vec2 p3=vec2(0.5+0.2*sin(t3),0.7+0.1*cos(t3));
vec2 p4=mouse;
vec3 accent=vec3(0.4235,0.3882,1.0);
float g1=orb(uv,p1,0.08,1.8);float g2=orb(uv,p2,0.1,1.6);
float g3=orb(uv,p3,0.06,2.0);float g4=orb(uv,p4,0.05,2.5)*0.3;
color+=accent*(g1+g2+g3+g4);
float v=1.0-length(uv-0.5)*1.2;color*=v;
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

function Login() {
    const [username, setUsername] = useState('')
    const [password, setPassword] = useState('')
    const [error, setError]       = useState('')
    const [loading, setLoading]   = useState(false)
    const { login } = useAuth()
    const navigate  = useNavigate()

    const handleSubmit = async (e) => {
        e.preventDefault()
        setError(''); setLoading(true)
        try {
            await login(username, password)
            navigate('/dashboard')
        } catch (err) {
            setError(err.response?.data?.detail || 'Login failed. Check your credentials.')
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
                        Unlock the Power<br />of Your Data
                    </h1>
                    <p className="auth-hero-subtitle">
                        Ask questions in plain English. Get instant AI-powered charts and insights — no SQL required.
                    </p>
                </div>
            </div>

            {/* ── Right: Login Form ── */}
            <div className="auth-form-panel">
                <div className="glass-panel auth-card">
                    {/* Logo */}
                    <div className="auth-logo-row">
                        <div className="auth-logo-icon">✦</div>
                        <div className="auth-logo-name">Aether AI</div>
                    </div>

                    {/* Error */}
                    {error && (
                        <div className="alert alert-error" style={{ marginBottom: '1.25rem' }}>
                            ⚠ {error}
                        </div>
                    )}

                    {/* Form */}
                    <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                        <div className="input-group" style={{ marginBottom: 0 }}>
                            <label htmlFor="username">Username</label>
                            <input
                                id="username"
                                className="input-field"
                                type="text"
                                value={username}
                                onChange={(e) => setUsername(e.target.value)}
                                placeholder="Enter your username"
                                required
                                autoComplete="username"
                            />
                        </div>
                        <div className="input-group" style={{ marginBottom: 0 }}>
                            <label htmlFor="password">Password</label>
                            <input
                                id="password"
                                className="input-field"
                                type="password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                placeholder="••••••••"
                                required
                                autoComplete="current-password"
                            />
                        </div>
                        <button
                            className="btn btn-primary"
                            type="submit"
                            disabled={loading}
                            style={{ width: '100%', marginTop: '0.5rem', padding: '0.8rem' }}
                        >
                            {loading ? (
                                <><div className="spinner" style={{ width: 18, height: 18 }} /> Signing in...</>
                            ) : (
                                'Sign In →'
                            )}
                        </button>
                    </form>

                    <div className="auth-footer">
                        Don't have an account? <Link to="/register">Register</Link>
                    </div>
                </div>
            </div>
        </div>
    )
}

export default Login
