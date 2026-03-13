'use client';

import { useSimulation } from '@/lib/store';
import Sidebar from '@/components/layout/Sidebar';
import Overview from '@/components/pages/Overview';
import Devices from '@/components/pages/Devices';
import NetworkMap from '@/components/pages/NetworkMap';
import Alerts from '@/components/pages/Alerts';
import EventsTimeline from '@/components/pages/EventsTimeline';
import AIAssistant from '@/components/pages/AIAssistant';
import Settings from '@/components/pages/Settings';

export default function Dashboard() {
  const { activeNav } = useSimulation();

  const renderPage = () => {
    switch (activeNav) {
      case 'overview': return <Overview />;
      case 'devices': return <Devices />;
      case 'network-map': return <NetworkMap />;
      case 'alerts': return <Alerts />;
      case 'events': return <EventsTimeline />;
      case 'ai-assistant': return <AIAssistant />;
      case 'settings': return <Settings />;
      default: return <Overview />;
    }
  };

  return (
    <div className="flex h-screen overflow-hidden cyber-grid">
      <Sidebar />
      <main className="flex-1 overflow-hidden flex flex-col">
        {renderPage()}
      </main>
    </div>
  );
}
