'use client';

import { useState, useRef, useEffect } from 'react';
import { useSimulation } from '@/lib/store';
import { Device } from '@/lib/types';
import { Bot, Send, User, Loader, Shield, Terminal } from 'lucide-react';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

function generateId() {
  return Math.random().toString(36).substring(2, 9);
}

const SUGGESTED_QUERIES = [
  'Which devices are risky?',
  'How many devices are on the network?',
  'Show me suspicious devices',
  'Why is CAM-LOBBY-21 flagged?',
  'What are the latest alerts?',
  'Which device has the lowest trust score?',
  'Show network status summary',
];

function generateResponse(query: string, devices: Device[], alerts: ReturnType<typeof useSimulation>['alerts']): string {
  const q = query.toLowerCase().trim();

  // How many devices
  if (q.includes('how many') && q.includes('device')) {
    const safe = devices.filter(d => d.riskLevel === 'safe').length;
    const suspicious = devices.filter(d => d.riskLevel === 'suspicious').length;
    const high = devices.filter(d => d.riskLevel === 'high-risk').length;
    return `Currently **${devices.length} devices** are connected to the network:\n• **${safe} Safe** — operating normally\n• **${suspicious} Suspicious** — elevated risk detected\n• **${high} High Risk** — immediate attention required\n\nThe network is ${high > 0 ? `⚠️ under active threat (${high} critical device${high > 1 ? 's' : ''})` : suspicious > 0 ? '🔶 showing anomalies' : '✅ operating normally'}.`;
  }

  // Risky / high risk devices
  if ((q.includes('risk') || q.includes('dangerous') || q.includes('compromised') || q.includes('critical')) && !q.includes('why')) {
    const high = devices.filter(d => d.riskLevel === 'high-risk');
    if (high.length === 0) return '✅ No high-risk devices detected at this time. The network appears secure.';
    const list = high.map(d =>
      `• **${d.name}** (${d.ip}) — Trust: ${Math.round(d.trustScore)}/100\n  ${d.flagReason?.substring(0, 80) || 'Behavioral anomaly detected'}…`
    ).join('\n\n');
    return `🚨 **${high.length} HIGH RISK device${high.length > 1 ? 's' : ''} detected:**\n\n${list}\n\nImmediate investigation recommended. Consider isolating these devices from the network.`;
  }

  // Suspicious devices
  if (q.includes('suspicious') || q.includes('anomal') || q.includes('unusual')) {
    const sus = devices.filter(d => d.riskLevel === 'suspicious');
    if (sus.length === 0) return '✅ No suspicious devices detected currently.';
    const list = sus.map(d =>
      `• **${d.name}** (${d.type}) — Trust: ${Math.round(d.trustScore)}/100 — ${d.ip}`
    ).join('\n');
    return `🔶 **${sus.length} suspicious device${sus.length > 1 ? 's' : ''} identified:**\n\n${list}\n\nThese devices are showing behavioral anomalies but have not been confirmed as compromised. Enhanced monitoring is active.`;
  }

  // Safe devices
  if (q.includes('safe') && !q.includes('not safe')) {
    const safe = devices.filter(d => d.riskLevel === 'safe');
    return `✅ **${safe.length} safe devices** are operating normally:\n\n${
      safe.slice(0, 6).map(d => `• ${d.name} (${d.type}) — ${d.ip} — Trust: ${Math.round(d.trustScore)}`).join('\n')
    }${safe.length > 6 ? `\n• … and ${safe.length - 6} more` : ''}`;
  }

  // Specific device query
  const deviceMatch = devices.find(d =>
    q.includes(d.name.toLowerCase()) ||
    q.includes(d.ip) ||
    q.includes(d.id.toLowerCase())
  );

  if (deviceMatch) {
    const riskEmoji = deviceMatch.riskLevel === 'safe' ? '✅' : deviceMatch.riskLevel === 'suspicious' ? '🔶' : '🚨';
    return `${riskEmoji} **${deviceMatch.name}** Analysis:\n\n**Type:** ${deviceMatch.type}\n**IP:** ${deviceMatch.ip}\n**Vendor:** ${deviceMatch.vendor}\n**Trust Score:** ${Math.round(deviceMatch.trustScore)}/100\n**Risk Level:** ${deviceMatch.riskLevel.toUpperCase()}\n**Traffic Rate:** ${deviceMatch.trafficRate.toFixed(1)} Mbps\n**Open Ports:** ${deviceMatch.ports.join(', ')}\n\n${deviceMatch.flagReason
      ? `**Security Analysis:**\n${deviceMatch.flagReason}`
      : 'No security issues detected for this device.'}`;
  }

  // Alerts query
  if (q.includes('alert')) {
    const recent = alerts.slice(0, 5);
    if (recent.length === 0) return '✅ No active alerts in the system.';
    const list = recent.map(a =>
      `• [${a.severity.toUpperCase()}] **${a.type}** — ${a.deviceName}\n  ${a.message.substring(0, 70)}…`
    ).join('\n\n');
    return `🔔 **${alerts.length} total alerts** — showing 5 most recent:\n\n${list}`;
  }

  // Network status
  if (q.includes('network') || q.includes('status') || q.includes('summary') || q.includes('overview')) {
    const high = devices.filter(d => d.riskLevel === 'high-risk').length;
    const suspicious = devices.filter(d => d.riskLevel === 'suspicious').length;
    const totalTraffic = devices.reduce((s, d) => s + d.trafficRate, 0);
    const avgTrust = devices.reduce((s, d) => s + d.trustScore, 0) / devices.length;
    const status = high > 0 ? '⚠️ THREAT DETECTED' : suspicious > 0 ? '🔶 ELEVATED RISK' : '✅ NORMAL';

    return `📊 **Network Status: ${status}**\n\n**Total Devices:** ${devices.length}\n**Average Trust Score:** ${Math.round(avgTrust)}/100\n**Total Traffic:** ${totalTraffic.toFixed(1)} Mbps\n**Active Alerts:** ${alerts.filter(a => !a.read).length}\n\n**Threat Breakdown:**\n• High Risk: ${high} device${high !== 1 ? 's' : ''}\n• Suspicious: ${suspicious} device${suspicious !== 1 ? 's' : ''}\n• Safe: ${devices.length - high - suspicious} devices\n\n${high > 0 ? '⚠️ Immediate action required for high-risk devices.' : suspicious > 0 ? '🔶 Monitor suspicious devices closely.' : '✅ No immediate threats detected.'}`;
  }

  // Lowest trust score
  if (q.includes('lowest') || q.includes('worst') || q.includes('most risky') || q.includes('most dangerous')) {
    const sorted = [...devices].sort((a, b) => a.trustScore - b.trustScore).slice(0, 3);
    const list = sorted.map((d, i) =>
      `${i + 1}. **${d.name}** — Trust: ${Math.round(d.trustScore)}/100 — ${d.riskLevel.toUpperCase()}`
    ).join('\n');
    return `📉 **Devices with lowest trust scores:**\n\n${list}\n\n${sorted[0].flagReason ? `\n**Top concern:** ${sorted[0].flagReason.substring(0, 100)}…` : ''}`;
  }

  // Traffic query
  if (q.includes('traffic')) {
    const sorted = [...devices].sort((a, b) => b.trafficRate - a.trafficRate).slice(0, 5);
    const list = sorted.map(d =>
      `• **${d.name}** — ${d.trafficRate.toFixed(1)} Mbps (${d.riskLevel})`
    ).join('\n');
    return `📶 **Top traffic consumers:**\n\n${list}`;
  }

  // Help
  if (q.includes('help') || q === '?' || q.includes('what can you')) {
    return `🤖 **IoT SecureNet AI Assistant**\n\nI can help you analyze your network security. Try asking:\n\n• "Which devices are risky?"\n• "Show me suspicious devices"\n• "Why is [device name] flagged?"\n• "How many devices are on the network?"\n• "What are the latest alerts?"\n• "Network status summary"\n• "Which device has the lowest trust score?"\n• "Show traffic usage"\n\nI have real-time access to all ${devices.length} connected devices.`;
  }

  // Default
  const high = devices.filter(d => d.riskLevel === 'high-risk').length;
  return `I analyzed your query against the current network state. Here's what I found:\n\n• **${devices.length} devices** currently monitored\n• **${high} high-risk** device${high !== 1 ? 's' : ''} requiring attention\n• **${alerts.filter(a => !a.read).length} unread alerts**\n\nFor more specific information, try asking about particular devices (by name or IP), risk levels, alerts, or network status. Type "help" for a full list of commands.`;
}

export default function AIAssistant() {
  const { devices, alerts } = useSimulation();
  const [messages, setMessages] = useState<Message[]>([
    {
      id: generateId(),
      role: 'assistant',
      content: `👋 **Welcome to IoT SecureNet AI Security Assistant**\n\nI'm monitoring **${devices.length} devices** in real time. I can help you:\n• Identify risky devices\n• Explain security alerts\n• Analyze device behavior\n• Provide network status summaries\n\nType a question or select a suggestion below to get started.`,
      timestamp: new Date(),
    },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMessage = async (text: string) => {
    if (!text.trim()) return;

    const userMsg: Message = {
      id: generateId(),
      role: 'user',
      content: text.trim(),
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    // Simulate AI processing delay
    await new Promise(r => setTimeout(r, 600 + Math.random() * 400));

    const response = generateResponse(text, devices, alerts);
    const assistantMsg: Message = {
      id: generateId(),
      role: 'assistant',
      content: response,
      timestamp: new Date(),
    };

    setMessages(prev => [...prev, assistantMsg]);
    setLoading(false);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    sendMessage(input);
  };

  return (
    <div className="h-full flex flex-col overflow-hidden">
      {/* Header */}
      <div className="px-6 py-3 border-b border-cyber-border bg-cyber-surface/60 flex-shrink-0">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-cyber-primary/10 border border-cyber-primary/30 flex items-center justify-center">
              <Bot size={18} className="text-cyber-primary" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-cyber-primary neon-text">AI Security Assistant</h1>
              <p className="text-xs text-cyber-muted">Powered by IoT behavioral analysis engine</p>
            </div>
          </div>
          <div className="flex items-center gap-2 text-xs">
            <span className="w-2 h-2 rounded-full bg-cyber-safe blink" />
            <span className="text-cyber-safe">Online</span>
            <span className="text-cyber-border mx-1">|</span>
            <Shield size={12} className="text-cyber-primary" />
            <span className="text-cyber-dim">{devices.length} devices indexed</span>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
        {messages.map(msg => (
          <div
            key={msg.id}
            className={`flex gap-3 fade-in-up ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}
          >
            {/* Avatar */}
            <div className={`
              flex-shrink-0 w-8 h-8 rounded-lg flex items-center justify-center
              ${msg.role === 'assistant'
                ? 'bg-cyber-primary/10 border border-cyber-primary/30'
                : 'bg-cyber-secondary/20 border border-cyber-secondary/30'
              }
            `}>
              {msg.role === 'assistant'
                ? <Bot size={14} className="text-cyber-primary" />
                : <User size={14} className="text-cyber-secondary" />
              }
            </div>

            {/* Bubble */}
            <div className={`
              max-w-[75%] rounded-xl px-4 py-3 text-sm
              ${msg.role === 'assistant'
                ? 'bg-cyber-card border border-cyber-border rounded-tl-none'
                : 'bg-cyber-secondary/15 border border-cyber-secondary/30 rounded-tr-none'
              }
            `}>
              <MarkdownText content={msg.content} />
              <div className="text-[10px] text-cyber-muted mt-1.5">
                {msg.timestamp.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
              </div>
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex gap-3">
            <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-cyber-primary/10 border border-cyber-primary/30 flex items-center justify-center">
              <Bot size={14} className="text-cyber-primary" />
            </div>
            <div className="bg-cyber-card border border-cyber-border rounded-xl rounded-tl-none px-4 py-3">
              <div className="flex items-center gap-2 text-cyber-muted text-sm">
                <Loader size={13} className="animate-spin text-cyber-primary" />
                <span>Analyzing network data…</span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Suggestions */}
      <div className="px-6 pb-2 flex-shrink-0">
        <div className="flex gap-2 overflow-x-auto pb-1 scrollbar-thin">
          {SUGGESTED_QUERIES.map(q => (
            <button
              key={q}
              onClick={() => sendMessage(q)}
              className="flex-shrink-0 px-3 py-1.5 text-xs bg-cyber-card border border-cyber-border rounded-full text-cyber-dim hover:text-cyber-primary hover:border-cyber-primary/40 transition-colors"
            >
              {q}
            </button>
          ))}
        </div>
      </div>

      {/* Input */}
      <div className="px-6 py-3 border-t border-cyber-border bg-cyber-surface/60 flex-shrink-0">
        <form onSubmit={handleSubmit} className="flex items-center gap-3">
          <div className="relative flex-1">
            <Terminal size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-cyber-muted" />
            <input
              ref={inputRef}
              type="text"
              value={input}
              onChange={e => setInput(e.target.value)}
              placeholder="Ask about devices, risks, alerts, network status…"
              disabled={loading}
              className="w-full pl-9 pr-4 py-2.5 text-sm bg-cyber-card border border-cyber-border rounded-xl text-cyber-text placeholder:text-cyber-muted focus:outline-none focus:border-cyber-primary/50 disabled:opacity-50 transition-colors"
            />
          </div>
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="p-2.5 rounded-xl bg-cyber-primary/15 border border-cyber-primary/40 text-cyber-primary hover:bg-cyber-primary/25 disabled:opacity-40 disabled:cursor-not-allowed transition-all"
          >
            <Send size={16} />
          </button>
        </form>
      </div>
    </div>
  );
}

// Simple markdown-like renderer
function MarkdownText({ content }: { content: string }) {
  const lines = content.split('\n');
  return (
    <div className="space-y-0.5 text-cyber-text leading-relaxed">
      {lines.map((line, i) => {
        if (!line) return <div key={i} className="h-1.5" />;

        // Bold text
        const rendered = line.replace(/\*\*(.*?)\*\*/g, '<strong class="text-cyber-primary font-semibold">$1</strong>');

        // Bullet point
        if (line.startsWith('• ') || line.startsWith('- ')) {
          return (
            <div key={i} className="flex gap-2">
              <span className="text-cyber-primary flex-shrink-0 mt-0.5">•</span>
              <span
                className="text-cyber-dim"
                dangerouslySetInnerHTML={{ __html: rendered.slice(2) }}
              />
            </div>
          );
        }

        // Numbered
        if (/^\d+\./.test(line)) {
          const [num, ...rest] = line.split('. ');
          return (
            <div key={i} className="flex gap-2">
              <span className="text-cyber-primary font-mono flex-shrink-0">{num}.</span>
              <span
                className="text-cyber-dim"
                dangerouslySetInnerHTML={{ __html: rest.join('. ').replace(/\*\*(.*?)\*\*/g, '<strong class="text-cyber-primary font-semibold">$1</strong>') }}
              />
            </div>
          );
        }

        return (
          <div
            key={i}
            className="text-cyber-dim"
            dangerouslySetInnerHTML={{ __html: rendered }}
          />
        );
      })}
    </div>
  );
}
