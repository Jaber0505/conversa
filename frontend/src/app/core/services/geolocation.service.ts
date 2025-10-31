import { Injectable } from '@angular/core';
import { Observable, from, of } from 'rxjs';
import { map, catchError } from 'rxjs/operators';

export interface GeolocationData {
  city: string;
  country: string;
  latitude: number;
  longitude: number;
}

export interface NearbyStats {
  city: string;
  activeMembers: number;
  upcomingEvents: number;
  languages: string[];
}

@Injectable({
  providedIn: 'root'
})
export class GeolocationService {

  /**
   * Récupère la position de l'utilisateur
   */
  getCurrentPosition(): Observable<GeolocationPosition> {
    return from(
      new Promise<GeolocationPosition>((resolve, reject) => {
        if (!navigator.geolocation) {
          reject(new Error('Geolocation not supported'));
          return;
        }

        navigator.geolocation.getCurrentPosition(resolve, reject, {
          timeout: 10000,
          maximumAge: 300000, // Cache 5 minutes
        });
      })
    );
  }

  /**
   * Récupère la ville à partir des coordonnées (via reverse geocoding)
   * Pour l'instant retourne des données mockées
   */
  getCityFromCoordinates(lat: number, lon: number): Observable<string> {
    // TODO: Appeler une vraie API de reverse geocoding (OpenStreetMap, Google, etc.)
    // Pour l'instant, retourne des villes aléatoires basées sur les coordonnées
    const cities = this.getMockCities(lat, lon);
    return of(cities[0]);
  }

  /**
   * Génère des statistiques fictives basées sur la localisation
   */
  getNearbyStats(city?: string): Observable<NearbyStats> {
    const defaultCity = city || 'Paris';
    const mockStats: NearbyStats = {
      city: defaultCity,
      activeMembers: Math.floor(Math.random() * 50) + 10, // 10-60 membres
      upcomingEvents: Math.floor(Math.random() * 8) + 3,   // 3-10 événements
      languages: this.getRandomLanguages()
    };

    return of(mockStats);
  }

  /**
   * Récupère ville + stats en une seule fois
   */
  getLocationWithStats(): Observable<NearbyStats> {
    return this.getCurrentPosition().pipe(
      map(position => ({
        lat: position.coords.latitude,
        lon: position.coords.longitude
      })),
      map(coords => {
        const city = this.getCityFromCoordinatesSync(coords.lat, coords.lon);
        return this.getNearbyStatsSync(city);
      }),
      catchError(() => {
        // Si géolocalisation échoue, utiliser des données par défaut
        return of(this.getNearbyStatsSync('Paris'));
      })
    );
  }

  // Méthodes privées utilitaires

  private getCityFromCoordinatesSync(lat: number, lon: number): string {
    const cities = this.getMockCities(lat, lon);
    return cities[0];
  }

  private getNearbyStatsSync(city: string): NearbyStats {
    return {
      city,
      activeMembers: Math.floor(Math.random() * 50) + 10,
      upcomingEvents: Math.floor(Math.random() * 8) + 3,
      languages: this.getRandomLanguages()
    };
  }

  private getMockCities(lat: number, lon: number): string[] {
    // Détection approximative basée sur les coordonnées
    if (lat > 48 && lat < 49 && lon > 2 && lon < 3) {
      return ['Paris', 'Île-de-France'];
    } else if (lat > 50 && lat < 51 && lon > 4 && lon < 5) {
      return ['Bruxelles', 'Belgique'];
    } else if (lat > 45 && lat < 46 && lon > 4 && lon < 5) {
      return ['Lyon', 'Rhône-Alpes'];
    } else if (lat > 43 && lat < 44 && lon > 5 && lon < 6) {
      return ['Marseille', 'Provence'];
    } else {
      // Ville par défaut si non reconnu
      return ['Paris', 'France'];
    }
  }

  private getRandomLanguages(): string[] {
    const allLanguages = [
      'Anglais', 'Espagnol', 'Allemand', 'Italien',
      'Portugais', 'Néerlandais', 'Arabe', 'Chinois',
      'Japonais', 'Russe'
    ];

    // Sélectionner 2-4 langues aléatoires
    const count = Math.floor(Math.random() * 3) + 2;
    const shuffled = allLanguages.sort(() => 0.5 - Math.random());
    return shuffled.slice(0, count);
  }
}
