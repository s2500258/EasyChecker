// Lightweight informational page about the EasyChecker service itself.
export default function AboutPage({ t }) {
  return (
    <section className="panel about-panel">
      <div className="panel-header">
        <h2>{t("aboutTitle")}</h2>
        <p>{t("aboutIntro")}</p>
      </div>

      <div className="about-content">
        <p>{t("aboutAuthor")}</p>
        <p>{t("aboutFunctionality")}</p>
      </div>
    </section>
  );
}
