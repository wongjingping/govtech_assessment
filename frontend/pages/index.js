import Head from 'next/head';
import Chat from '../components/Chat';

export default function Home() {
  return (
    <div className="min-h-screen bg-gray-50">
      <Head>
        <title>HDB Resale Price Chat</title>
        <meta name="description" content="Chat interface for HDB resale price analysis" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <main>
        <div className="container mx-auto max-w-4xl">
          <header className="py-6 px-4 border-b bg-white">
            <h1 className="text-2xl font-bold text-center">HDB Resale Price Assistant</h1>
            <p className="text-center text-gray-600 mt-2">
              Ask questions about HDB resale prices, market trends, and predictions
            </p>
          </header>
          
          <Chat />
        </div>
      </main>

      <footer className="py-4 border-t text-center text-gray-500 text-sm">
        <p>HDB Resale Price Analysis System</p>
      </footer>
    </div>
  );
} 