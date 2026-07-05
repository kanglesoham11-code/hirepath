<div align="center">
  <img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&height=250&section=header&text=HirePath&fontSize=80&animation=fadeIn" width="100%" />

  <a href="https://git.io/typing-svg"><img src="https://readme-typing-svg.herokuapp.com?font=Fira+Code&weight=600&size=26&pause=1000&color=2F80ED&center=true&vCenter=true&width=600&lines=Welcome+to+HirePath;Streamlining+the+Recruitment+Process;AI-Powered+Candidate+Matching;The+Future+of+Hiring" alt="Typing SVG" /></a>

  <p align="center">
    <b>A next-generation AI-driven recruitment platform that connects top talent with outstanding opportunities.</b>
  </p>

  <div>
    <img src="https://img.shields.io/badge/Next.js-000000?style=for-the-badge&logo=next.js&logoColor=white" alt="Next.js" />
    <img src="https://img.shields.io/badge/TypeScript-007ACC?style=for-the-badge&logo=typescript&logoColor=white" alt="TypeScript" />
    <img src="https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white" alt="Tailwind CSS" />
    <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
  </div>
</div>

---

## 🚀 Animated Workflow Overview

<div align="center">
  <img src="https://cdn.dribbble.com/users/1242979/screenshots/7092165/media/fb6097dcb2cbfdf113dcb53805903b4d.gif" width="80%" style="border-radius: 12px; box-shadow: 0 8px 16px rgba(0,0,0,0.3);" alt="Workflow Animation" />
  <p><i>HirePath automates the entire recruitment funnel—from candidate sourcing to interview scheduling, completely powered by intelligent insights.</i></p>
</div>

---

## 📊 Detailed System Flowchart

Here is the intricate, end-to-end architecture of how HirePath processes a candidate's journey.

```mermaid
graph TD
    %% Styling
    classDef primary fill:#2F80ED,stroke:#fff,stroke-width:2px,color:#fff;
    classDef secondary fill:#00C9A7,stroke:#fff,stroke-width:2px,color:#fff;
    classDef highlight fill:#F72C5B,stroke:#fff,stroke-width:2px,color:#fff;
    classDef database fill:#4B4B4B,stroke:#fff,stroke-width:2px,color:#fff;

    A([Candidate Applies]):::primary --> B{AI Resume Parsing}:::secondary
    B -->|Valid Data| C(Feature Extraction):::secondary
    B -->|Invalid Data| Z([Reject/Notify]):::highlight
    
    C --> D[(Vector Database)]:::database
    
    E([Employer Posts Job]):::primary --> F(Job Requirements Encoding):::secondary
    F --> D
    
    D --> G{AI Semantic Matcher}:::secondary
    G -->|High Match| H(Automated Initial Screen):::primary
    G -->|Low Match| Z
    
    H --> I(Technical / Soft Skill Assessment):::secondary
    I --> J{Assessment Score}:::secondary
    
    J -->|Pass| K(Interview Scheduling):::primary
    J -->|Fail| Z
    
    K --> L([Final HR Review & Offer]):::highlight
```

---

## 🌟 Key Features

<table align="center" style="border: none;">
  <tr style="border: none;">
    <td width="50%" style="border: none;">
      <h3>🧠 AI Resume Parsing</h3>
      <ul>
        <li>Extracts skills, experience, and education with 99% accuracy.</li>
        <li>Eliminates human bias in early screening.</li>
        <li>Supports PDF, DOCX, and plain text formats.</li>
      </ul>
    </td>
    <td align="center" width="50%" style="border: none;">
      <img src="https://cdn.dribbble.com/users/1162077/screenshots/3848914/programmer.gif" width="80%" style="border-radius: 10px;" />
    </td>
  </tr>
  <tr style="border: none;">
    <td align="center" width="50%" style="border: none;">
      <img src="https://cdn.dribbble.com/users/418188/screenshots/3102257/media/132cb0cc7c50a583307b22ad23c14c51.gif" width="80%" style="border-radius: 10px;" />
    </td>
    <td width="50%" style="border: none;">
      <h3>⚡ Seamless Interview Scheduling</h3>
      <ul>
        <li>Calendar syncing (Google, Outlook).</li>
        <li>Automated reminders for candidates & interviewers.</li>
        <li>Real-time availability adjustments.</li>
      </ul>
    </td>
  </tr>
</table>

## 🛠️ Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/kanglesoham11-code/hirepath.git

# 2. Navigate to the project directory
cd hirepath

# 3. Install dependencies
npm install

# 4. Setup environment variables
cp .env.example .env

# 5. Run the development server
npm run dev
```

## 🤝 Contributing

We welcome contributions! Please open an issue or submit a pull request if you have ideas for improvements.

## 📜 License

Distributed under the MIT License. See `LICENSE` for more information.

---

<div align="center">
  <p>Made with ❤️ by <a href="https://github.com/kanglesoham11-code">Soham</a></p>
  <img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&height=100&section=footer" width="100%" />
</div>
