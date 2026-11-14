import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import React from 'react';
import { Header } from '../components/Header';
import { ChatWorkspace } from '../components/ChatWorkspace';
import { KnowledgeLibrary } from '../components/KnowledgeLibrary';
import { RetrievalInspector } from '../components/RetrievalInspector';
import { SettingsPanel } from '../components/SettingsPanel';
import { ApiService } from '../services/api';

describe('OmniMind AI Frontend Component Tests', () => {
  const mockHealth = {
    app_name: 'OmniMind AI',
    version: '2.0.0',
    tagline: 'One AI. Every Modality. All Your Knowledge.',
    providers: {
      groq: {
        provider: 'Groq Cloud',
        configured: true,
        status: 'online',
        chat_models: ['llama-3.3-70b-versatile'],
        vision_models: ['llama-3.2-90b-vision-preview'],
        audio_models: ['whisper-large-v3-turbo'],
      },
      gemini: {
        provider: 'Google Gemini',
        configured: true,
        status: 'online',
        chat_models: ['gemini-1.5-flash'],
        vision_models: ['gemini-1.5-flash'],
        audio_models: [],
      },
    },
    supported_modalities: ['text', 'pdf', 'docx', 'pptx', 'csv', 'xlsx', 'image', 'audio'],
  };

  it('renders Header with OmniMind AI branding and navigation tabs', () => {
    render(
      <Header
        health={mockHealth}
        activeTab="chat"
        setActiveTab={() => {}}
        selectedProvider="gemini"
        setSelectedProvider={() => {}}
      />
    );

    expect(screen.getByText('OmniMind')).toBeInTheDocument();
    expect(screen.getByText(/AI v2.0/i)).toBeInTheDocument();
    expect(screen.getByText('Chat Assistant')).toBeInTheDocument();
    expect(screen.getByText('Knowledge Library')).toBeInTheDocument();
    expect(screen.getByText('RAG Inspector')).toBeInTheDocument();
    expect(screen.getByText('Settings')).toBeInTheDocument();
  });

  it('renders ChatWorkspace with welcome message and input controls', () => {
    render(
      <ChatWorkspace
        provider="gemini"
        sessionId="test_sess"
        uploadedDocs={[]}
        onRefreshDocs={() => {}}
      />
    );

    expect(screen.getByText(/OmniMind AI/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/Ask a question/i)).toBeInTheDocument();
    expect(screen.getByTitle(/Attach Document/i)).toBeInTheDocument();
    expect(screen.getByTitle(/Attach Image/i)).toBeInTheDocument();
    expect(screen.getByTitle(/Record Audio/i)).toBeInTheDocument();
  });

  it('sends chat message and renders grounded RAG citations', async () => {
    vi.spyOn(ApiService, 'chat').mockResolvedValue({
      answer: 'According to page 4 of the financial report, revenue grew 30%.',
      citations: [
        {
          source: 'annual_report.pdf',
          location: 'Page/Unit 4',
          file_type: 'PDF',
          similarity_score: 0.88,
          snippet: 'Revenue grew 30% in Q4 reaching $50M...',
        },
      ],
      model: 'gemini-1.5-flash',
      provider: 'gemini',
      context_used: true,
    });

    render(
      <ChatWorkspace
        provider="gemini"
        sessionId="test_sess"
        uploadedDocs={[{ document_id: '1', filename: 'annual_report.pdf', chunk_count: 5, source: 'annual_report.pdf' }]}
        onRefreshDocs={() => {}}
      />
    );

    const input = screen.getByPlaceholderText(/Ask a question/i);
    fireEvent.change(input, { target: { value: 'What was the revenue growth?' } });
    fireEvent.keyDown(input, { key: 'Enter', code: 'Enter' });

    await waitFor(() => {
      expect(screen.getAllByText(/revenue grew 30%/i).length).toBeGreaterThanOrEqual(1);
      expect(screen.getByText('annual_report.pdf')).toBeInTheDocument();
      expect(screen.getByText('Page/Unit 4')).toBeInTheDocument();
    });
  });

  it('renders KnowledgeLibrary with drag-and-drop zone and supported formats', () => {
    render(
      <KnowledgeLibrary
        provider="gemini"
        sessionId="test_sess"
        docs={[
          { document_id: 'doc_1', filename: 'research_paper.pdf', chunk_count: 8, source: 'research_paper.pdf' },
        ]}
        onRefresh={() => {}}
      />
    );

    expect(screen.getByText('Upload Knowledge Documents')).toBeInTheDocument();
    expect(screen.getByText('PDF')).toBeInTheDocument();
    expect(screen.getByText('DOCX')).toBeInTheDocument();
    expect(screen.getByText('PPTX')).toBeInTheDocument();
    expect(screen.getByText('research_paper.pdf')).toBeInTheDocument();
    expect(screen.getByText('8 semantic chunks indexed')).toBeInTheDocument();
  });

  it('renders RetrievalInspector and handles query search', async () => {
    vi.spyOn(ApiService, 'searchRetrieval').mockResolvedValue([
      {
        content: 'Artificial neural networks use gradient descent backpropagation.',
        similarity_score: 0.92,
        metadata: { source: 'deep_learning.pdf', page: 12 },
      },
    ]);

    render(<RetrievalInspector provider="gemini" sessionId="test_sess" />);

    const searchInput = screen.getByPlaceholderText(/Enter a test query/i);
    fireEvent.change(searchInput, { target: { value: 'neural networks' } });
    fireEvent.click(screen.getByRole('button', { name: /Inspect Retrieval/i }));

    await waitFor(() => {
      expect(screen.getByText(/Artificial neural networks/i)).toBeInTheDocument();
      expect(screen.getByText(/92.0%/i)).toBeInTheDocument();
    });
  });

  it('renders SettingsPanel with API URL configuration and provider cards', () => {
    render(<SettingsPanel health={mockHealth} onRefreshHealth={() => {}} />);

    expect(screen.getByText('Backend API Endpoint')).toBeInTheDocument();
    expect(screen.getByText('Google Gemini')).toBeInTheDocument();
    expect(screen.getByText('Groq Cloud')).toBeInTheDocument();
    expect(screen.getByText(/Session Scoping & Data Retention Notice/i)).toBeInTheDocument();
  });
});
