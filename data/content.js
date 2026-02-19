export const siteConfig = {
  name: 'Sergio E. Mares',
  shortName: 'Sergio',
  title: 'Computational Biology Ph.D. Candidate',
  email: 'sergio.mares@berkeley.edu',
  social: {
    github: 'https://github.com/sermare',
    scholar:
      'https://scholar.google.com/citations?user=RtKyA3wAAAAJ&hl=en',
    linkedin: 'https://www.linkedin.com/in/sergio-mares/',
    twitter: 'https://x.com/sergiomaresd',
    lichess: 'https://lichess.org/@/sensaciondelbosque',
  },
};

export const navTabs = [
  { label: 'Home', path: '/' },
  { label: 'Research', path: '/research' },
  { label: 'Writing', path: '/writing' },
  { label: 'Reading', path: '/reading' },
  { label: 'Hobbies', path: '/hobbies' },
];

export const featured = [
  {
    ordering: 1,
    card: {
      id: 'intro',
      type: 'intro',
      large: true,
    },
  },
  {
    ordering: 2,
    card: {
      id: 'pmhc-binding',
      type: 'research',
      large: true,
      published_at: '2025-07-01',
      properties: {
        name: 'Continued domain-specific pre-training of protein language models for pMHC-I binding prediction',
        shortName: 'pMHC-I Binding Prediction',
        venue: 'MLCB 2025',
        authors: 'Sergio E. Mares, Ariel Espinoza, Nilah M. Ioannidis',
        description:
          'Testing whether domain-specific continued pre-training of protein language models improves pMHC-I binding affinity prediction, starting from ESM Cambrian (300M parameters).',
        imageUrl: '/images/epitope_mhc_rotating.gif',
        link: {
          url: 'https://arxiv.org/abs/2507.13077v1',
          tooltipLabel: 'arXiv',
        },
        tags: [
          { color: 'sky', label: 'Protein LMs' },
          { color: 'purple', label: 'Immunology' },
        ],
      },
    },
  },
  {
    ordering: 3,
    card: {
      id: 'diffusion-pmhc',
      type: 'research',
      large: false,
      published_at: '2025-07-01',
      properties: {
        name: 'Generation of structure-guided pMHC-I libraries using Diffusion Models',
        shortName: 'pMHC-I Diffusion Models',
        venue: 'ICML 2025 Workshop',
        authors: 'Sergio E. Mares, Ariel Espinoza, Nilah M. Ioannidis',
        description:
          'Structure-guided benchmark of pMHC-I peptides designed using diffusion models conditioned on crystal structure interaction distances.',
        link: {
          url: 'https://arxiv.org/abs/2507.08902',
          tooltipLabel: 'arXiv',
        },
        tags: [
          { color: 'orange', label: 'Diffusion' },
          { color: 'sky', label: 'Structural' },
        ],
      },
    },
  },
  {
    ordering: 4,
    card: {
      id: 'chess',
      type: 'hobbies',
      large: false,
      properties: {
        label: 'Chess',
        cardStyle: 'text',
        properties: {
          heading: 'Chess',
          subheading: 'sensaciondelbosque',
          body: "I've been playing chess since I moved to the US. Find me on Lichess!",
          tags: [{ color: 'amber', label: 'Rapid' }, { color: 'lime', label: 'Blitz' }],
        },
        link: {
          url: 'https://lichess.org/@/sensaciondelbosque',
          tooltipLabel: 'Lichess',
        },
      },
    },
  },
  {
    ordering: 5,
    card: {
      id: 'bioemu-post',
      type: 'writing',
      large: false,
      published_at: '2025-11-25',
      properties: {
        type: 'Blog',
        title: 'BioEMU Deep Dive: From Discussion to Research Vision',
        url: '#',
        publishedOn: 'November 25, 2025',
        contentPreview:
          'A comprehensive exploration of protein ensemble modeling, molecular dynamics integration, and the future of structural biology through the lens of a Microsoft Research internship interview.',
      },
    },
  },
  {
    ordering: 6,
    card: {
      id: 'efhp-calcium',
      type: 'research',
      large: false,
      published_at: '2022-05-01',
      properties: {
        name: 'EF-hand protein, EfhP, specifically binds Ca²⁺ and mediates Ca²⁺ regulation of virulence',
        shortName: 'EfhP Ca²⁺ Signaling',
        venue: 'Nature Scientific Reports 2022',
        authors:
          'Biraj B. Kayastha, ... Sergio E. Mares, et al.',
        description:
          'Studying the putative Ca²⁺-binding protein EfhP and its role in calcium-mediated regulation of virulence in Pseudomonas aeruginosa.',
        imageUrl: '/images/pseudomonas.gif',
        link: {
          url: 'https://doi.org/10.1038/s41598-022-12584-9',
          tooltipLabel: 'DOI',
        },
        tags: [
          { color: 'lime', label: 'Microbiology' },
          { color: 'orange', label: 'Calcium' },
        ],
      },
    },
  },
  {
    ordering: 7,
    card: {
      id: 'design-everyday',
      type: 'reading',
      large: false,
      properties: {
        type: 'Books',
        title: 'The Emperor of All Maladies',
        author: 'Siddhartha Mukherjee',
        tags: [{ color: 'green', label: 'FINISHED' }],
        link: {
          url: 'https://www.goodreads.com/book/show/7170627-the-emperor-of-all-maladies',
          tooltipLabel: 'Goodreads',
        },
      },
    },
  },
  {
    ordering: 8,
    card: {
      id: 'carp-biomarker',
      type: 'research',
      large: false,
      published_at: '2020-01-01',
      properties: {
        name: 'carP, encoding a Ca²⁺-regulated putative phytase, is evolutionarily conserved in P. aeruginosa',
        shortName: 'carP Biomarker',
        venue: 'Journal of Microbiology 2020',
        authors: 'Sergio E. Mares, M. King, A. Kubo, et al.',
        description:
          'Studying the conservation of carP and its potential as a biomarker for Pseudomonas aeruginosa.',
        link: {
          url: 'https://doi.org/10.1099/mic.0.001004',
          tooltipLabel: 'DOI',
        },
        tags: [
          { color: 'lime', label: 'Genomics' },
          { color: 'purple', label: 'Biomarker' },
        ],
      },
    },
  },
  {
    ordering: 9,
    card: {
      id: 'baculovirus',
      type: 'research',
      large: false,
      published_at: '2021-06-01',
      properties: {
        name: 'Baculovirus ARIF-1 induces the formation of dynamic clusters of invadosome structures',
        shortName: 'Baculovirus ARIF-1',
        venue: 'Molecular Biology of the Cell 2021',
        authors: 'Domokos I. Lauko, Taro Ohkawa, Sergio E. Mares, Matthew D. Welch',
        description:
          'Investigating how AcMNPV protein ARIF-1 induces formation of cortical concentrations of polymerized actin in insect cells.',
        link: {
          url: 'https://doi.org/10.1091/mbc.E20-11-0705',
          tooltipLabel: 'DOI',
        },
        tags: [
          { color: 'sky', label: 'Cell Bio' },
          { color: 'orange', label: 'Virology' },
        ],
      },
    },
  },
  {
    ordering: 10,
    card: {
      id: 'myxococcota',
      type: 'research',
      large: false,
      published_at: '2021-01-01',
      properties: {
        name: 'Genomes of novel Myxococcota reveal severely curtailed machineries for predation',
        shortName: 'Myxococcota Genomes',
        venue: 'Environmental Microbiology 2021',
        authors: 'Chelsea L. Murphy, ... Sergio E. Mares, et al.',
        description:
          'Analysis of 13 distinct pathways crucial to predation and cellular differentiation in novel Myxococcota genomes.',
        link: {
          url: 'https://journals.asm.org/doi/10.1128/aem.01706-21',
          tooltipLabel: 'DOI',
        },
        tags: [
          { color: 'lime', label: 'Metagenomics' },
          { color: 'purple', label: 'Evolution' },
        ],
      },
    },
  },
  {
    ordering: 11,
    card: {
      id: 'deep-learning-life',
      type: 'reading',
      large: false,
      properties: {
        type: 'Books',
        title: 'Deep Learning',
        author: 'Ian Goodfellow, Yoshua Bengio & Aaron Courville',
        tags: [{ color: 'amber', label: 'READING' }],
        link: {
          url: 'https://www.deeplearningbook.org/',
          tooltipLabel: 'Website',
        },
      },
    },
  },
  {
    ordering: 12,
    card: {
      id: 'coding-hobby',
      type: 'hobbies',
      large: false,
      properties: {
        label: 'Coding',
        cardStyle: 'text',
        properties: {
          heading: 'Open Source',
          subheading: 'github.com/sermare',
          body: 'Building tools at the intersection of ML and biology. Check out my projects on GitHub.',
          tags: [
            { color: 'sky', label: 'Python' },
            { color: 'orange', label: 'ML' },
          ],
        },
        link: {
          url: 'https://github.com/sermare',
          tooltipLabel: 'GitHub',
        },
      },
    },
  },
];
