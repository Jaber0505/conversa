import React, { useEffect, useState } from 'react';

function PingTest() {
  const [response, setResponse] = useState(null);
  const API_URL = process.env.REACT_APP_API_URL;

  useEffect(() => {
    fetch(`${API_URL}/api/ping/`)
      .then(res => {
        if (!res.ok) throw new Error("Réponse non valide");
        return res.json();
      })
      .then(data => setResponse(data.message))
      .catch(err => setResponse("❌ Erreur de connexion"));
  }, [API_URL]);

  return (
    <div>
      <h3>Test de connexion API</h3>
      <p>Résultat : {response || "⏳ En attente..."}</p>
    </div>
  );
}

export default PingTest;
