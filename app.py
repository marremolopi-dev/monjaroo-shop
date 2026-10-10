# =============================================================
#  Monjaroo.shop — app.py v15
#  + Galerie 5 photos par produit avec carrousel auto
# =============================================================

from flask import (Flask, render_template, request, redirect, url_for,
                   session, flash, jsonify, make_response, g)
from flask_sqlalchemy import SQLAlchemy
from flask_login import (LoginManager, UserMixin, login_user,
                         login_required, logout_user, current_user)
from jinja2 import DictLoader
from datetime import datetime, timedelta
from urllib.parse import quote
from werkzeug.security import generate_password_hash, check_password_hash
import re, os, uuid, csv, io, base64
import urllib.request
import json as _json

# =============================================================
# CHEMINS
# =============================================================
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, "static", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
ALLOWED_EXT = {"png", "jpg", "jpeg", "gif", "webp", "svg"}
MAX_PHOTOS_PAR_PRODUIT = 5


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-moi-en-prod-!!!")
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(BASE_DIR, "monjaroo.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    ADMIN_USERNAME = "admin"
    ADMIN_EMAIL = "admin@monjaroo.shop"
    ADMIN_PASSWORD = "admin123"

    SITE_NAME = "Monjaroo.shop"
    SITE_DESCRIPTION = ("Boutique en ligne de produits de bien-être, "
                        "peptides, médicaments et pilules. Livraison discrète.")
    SITE_KEYWORDS = "monjaroo, peptides, médicaments, pilules, bien-être"
    SITE_EMAIL = "info@monjaroo.shop"
    SITE_PHONE = "+33 6 44 69 06 92"
    SITE_COUNTRY = "France"
    SITE_FLAG = "🇫🇷"
    SITE_URL = os.environ.get("SITE_URL", "http://127.0.0.1:5000")

    WHATSAPP_NUMBER = "33644690692"
    WHATSAPP_MESSAGE = "Bonjour, je souhaite des informations sur vos produits Monjaroo.shop"

    UPLOAD_FOLDER = UPLOAD_DIR
    MAX_PHOTOS = MAX_PHOTOS_PAR_PRODUIT

    LANGUAGES = {
        "fr": ("Français", "🇫🇷"),
        "en": ("English", "🇬🇧"),
        "nl": ("Nederlands", "🇳🇱"),
        "de": ("Deutsch", "🇩🇪"),
        "it": ("Italiano", "🇮🇹"),
        "es": ("Español", "🇪🇸"),
    }
    DEFAULT_LANG = "fr"


app = Flask(__name__)
app.config.from_object(Config)
app.permanent_session_lifetime = timedelta(days=30)

# =============================================================
# FAVICON
# =============================================================
FAVICON_SVG = """<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 320 320'><rect width='320' height='320' rx='48' fill='#ffffff'/><g transform='translate(160,110)'><circle cx='0' cy='0' r='62' fill='#0d5e5e'/><path d='M-30 -6 h60 M-6 -30 v60' stroke='#ffffff' stroke-width='14' stroke-linecap='round'/><path d='M12 18 c -22 4 -30 22 -14 40 c 12 14 30 8 26 -8 c -3 -12 -18 -14 -22 -4' stroke='#7dd3a0' stroke-width='6' fill='none' stroke-linecap='round'/></g><text x='160' y='240' text-anchor='middle' font-family='Arial Black, Impact, sans-serif' font-size='56' font-weight='900' fill='#0d5e5e'>MONJAROO</text><text x='160' y='280' text-anchor='middle' font-family='Arial, sans-serif' font-size='22' font-weight='700' fill='#a855f7' letter-spacing='4'>.SHOP</text></svg>"""
FAVICON_B64 = base64.b64encode(FAVICON_SVG.encode("utf-8")).decode("ascii")

# =============================================================
# ICONES SVG
# =============================================================
ICONS = {
    "home": "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'><path d='M3 9.5 12 3l9 6.5V20a1 1 0 0 1-1 1h-5v-7h-6v7H4a1 1 0 0 1-1-1z'/></svg>",
    "tag": "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'><path d='M20.59 13.41 12 22l-9-9V4h9z'/><circle cx='7.5' cy='7.5' r='1.5' fill='currentColor'/></svg>",
    "truck": "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'><path d='M1 3h13v13H1z'/><path d='M14 8h4l3 3v5h-7z'/><circle cx='5.5' cy='18.5' r='2'/><circle cx='17.5' cy='18.5' r='2'/></svg>",
    "support": "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'><path d='M4 14v-2a8 8 0 1 1 16 0v2'/><path d='M4 14a2 2 0 0 1 2-2h1v6H6a2 2 0 0 1-2-2z'/><path d='M20 14a2 2 0 0 0-2-2h-1v6h1a2 2 0 0 0 2-2z'/></svg>",
    "cart": "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'><circle cx='9' cy='20' r='1.5'/><circle cx='18' cy='20' r='1.5'/><path d='M2 3h3l2.4 12.4a2 2 0 0 0 2 1.6h8.7a2 2 0 0 0 2-1.6L22 7H6'/></svg>",
    "user": "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'><circle cx='12' cy='8' r='4'/><path d='M4 21a8 8 0 0 1 16 0'/></svg>",
    "search": "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'><circle cx='11' cy='11' r='7'/><path d='m20 20-3.5-3.5'/></svg>",
    "star": "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='#f5b301'><path d='m12 2 3 6.6 7.2.7-5.5 4.9L18.5 22 12 18.3 5.5 22l1.8-7.8L1.8 9.3 9 8.6z'/></svg>",
    "star-o": "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='#f5b301' stroke-width='1.5'><path d='m12 2 3 6.6 7.2.7-5.5 4.9L18.5 22 12 18.3 5.5 22l1.8-7.8L1.8 9.3 9 8.6z'/></svg>",
    "globe": "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='1.6' stroke-linecap='round' stroke-linejoin='round'><circle cx='12' cy='12' r='9'/><path d='M3 12h18'/><path d='M12 3a14 14 0 0 1 0 18 14 14 0 0 1 0-18z'/></svg>",
    "chevron": "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><path d='m6 9 6 6 6-6'/></svg>",
    "menu": "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round'><path d='M4 6h16M4 12h16M4 18h16'/></svg>",
    "close": "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2' stroke-linecap='round'><path d='M6 6l12 12M6 18L18 6'/></svg>",
    "mail": "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'><rect x='3' y='5' width='18' height='14' rx='2'/><path d='m3 7 9 6 9-6'/></svg>",
    "phone": "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'><path d='M22 16.9v3a2 2 0 0 1-2.2 2 19.8 19.8 0 0 1-8.6-3 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.1 4.2 2 2 0 0 1 4.1 2h3a2 2 0 0 1 2 1.7c.1 1 .4 2 .7 2.9a2 2 0 0 1-.5 2.1L8.1 9.9a16 16 0 0 0 6 6l1.2-1.2a2 2 0 0 1 2.1-.5c.9.3 1.9.6 2.9.7a2 2 0 0 1 1.7 2z'/></svg>",
    "whatsapp": "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32' fill='currentColor'><path d='M16.003 3C8.832 3 3 8.83 3 16c0 2.29.6 4.53 1.74 6.5L3 29l6.66-1.74a13.03 13.03 0 0 0 6.34 1.62h.005C23.174 28.88 29 23.05 29 15.88 29 8.71 23.174 3 16.003 3zm0 23.74h-.004a10.8 10.8 0 0 1-5.5-1.5l-.395-.235-4.09 1.07 1.09-3.98-.257-.41a10.77 10.77 0 0 1-1.65-5.74c0-5.96 4.85-10.81 10.81-10.81 2.89 0 5.6 1.13 7.64 3.17a10.74 10.74 0 0 1 3.17 7.65c0 5.96-4.85 10.81-10.81 10.81zm5.93-8.1c-.325-.163-1.92-.947-2.218-1.055-.297-.108-.513-.163-.73.163-.216.325-.838 1.055-1.027 1.272-.19.216-.379.244-.704.082-.325-.163-1.373-.506-2.616-1.614-.967-.863-1.62-1.93-1.81-2.255-.19-.325-.02-.5.142-.663.146-.145.325-.379.488-.568.163-.19.216-.325.325-.542.108-.216.054-.406-.027-.568-.082-.163-.73-1.76-1-2.41-.264-.632-.532-.546-.73-.556l-.622-.011a1.19 1.19 0 0 0-.866.406c-.297.325-1.135 1.11-1.135 2.705 0 1.596 1.162 3.137 1.324 3.353.163.216 2.287 3.49 5.54 4.895.774.335 1.379.535 1.85.685.778.247 1.486.213 2.046.13.624-.093 1.92-.785 2.19-1.543.271-.758.271-1.407.19-1.543-.082-.135-.297-.216-.622-.379z'/></svg>",
    "heart": "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'><path d='M12 21s-7-4.5-9-9.5C1.5 8 3.5 4.5 7 4.5c2 0 3.5 1 5 3 1.5-2 3-3 5-3 3.5 0 5.5 3.5 4 7-2 5-9 9.5-9 9.5z'/></svg>",
    "eye": "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'><path d='M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z'/><circle cx='12' cy='12' r='3'/></svg>",
    "eye-off": "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'><path d='M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24'/><path d='M1 1l22 22'/></svg>",
    "check": "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round'><path d='m4 12 5 5 11-11'/></svg>",
    "shield": "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'><path d='M12 3 4 6v6c0 5 3.5 8.5 8 9 4.5-.5 8-4 8-9V6z'/><path d='m9 12 2 2 4-4'/></svg>",
    "camera": "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'><path d='M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z'/><circle cx='12' cy='13' r='4'/></svg>",
    "trash": "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='1.8' stroke-linecap='round' stroke-linejoin='round'><path d='M3 6h18M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2m3 0v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6h14z'/></svg>",
}

# =============================================================
# TRADUCTIONS
# =============================================================
T = {
    "fr": {
        "welcome": "Bienvenue dans la boutique Monjaroo",
        "hero_title": "Produits de bien-être haut de gamme pour la santé quotidienne",
        "hero_text": "Découvrez des compléments alimentaires et produits de bien-être de qualité supérieure, rigoureusement testés et approuvés, pour soutenir votre corps, stimuler votre énergie et favoriser une vitalité durable.",
        "buy_now": "Achetez maintenant",
        "search": "Rechercher", "search_ph": "Rechercher un produit...",
        "login": "Se connecter", "register": "S'inscrire", "logout": "Se déconnecter",
        "account": "Mon compte", "cart": "Panier", "empty_cart": "Votre panier est vide.",
        "home": "Accueil", "meds": "Médicaments", "peptides": "Peptides",
        "pills": "Pilules pour l'érection", "general": "Général",
        "blog": "Blog", "contact": "Contact",
        "cgv": "Conditions générales", "returns": "Retours et remboursements",
        "privacy": "Politique de confidentialité", "fair": "Questions équitables",
        "faq": "Foire aux questions",
        "reviews": "Avis clients", "reviews_title": "Ce que disent nos clients",
        "leave_review": "Laissez votre avis", "post_review": "Publier mon avis",
        "add_to_cart": "Ajouter au panier", "your_cart": "Votre panier",
        "checkout": "Passer commande", "order_wa": "Commander via WhatsApp",
        "features_home": "Magasin fiable proposant des produits de qualité.",
        "features_price": "Des prix abordables et attractifs pour tous les clients.",
        "features_ship": "Livraison express gratuite avec suivi.",
        "features_support": "Assistance en ligne 24h/24 et 7j/7.",
        "newsletter": "Bénéficiez de 10 % de réduction sur votre prochaine commande",
        "newsletter_sub": "Inscrivez-vous à notre newsletter pour recevoir nos offres exclusives.",
        "subscribe": "S'inscrire", "email_ph": "Votre adresse e-mail",
        "about_us": "À propos de nous", "about_title": "Promouvoir la santé par la qualité et les soins",
        "about_text": "Chez Monjaroo.shop, nous croyons que la véritable santé commence par la confiance.",
        "discover": "Découvrez nos peptides et médicaments",
        "contact_us": "Contactez-nous", "all_rights": "Tous droits réservés",
        "full_name": "Nom complet", "email": "Email", "phone": "Téléphone",
        "address": "Adresse de livraison", "password": "Mot de passe",
        "confirm_password": "Confirmer le mot de passe",
        "send": "Envoyer", "message": "Message", "total": "Total", "quantity": "Quantité",
        "welcome_back": "Bon retour !", "invalid_credentials": "Email ou mot de passe incorrect.",
        "email_exists": "Cet email est déjà utilisé.",
        "account_created": "Compte créé avec succès !",
        "passwords_dont_match": "Les mots de passe ne correspondent pas.",
        "you_are_logged": "Vous êtes connecté.",
        "order_info_title": "Vos informations de livraison",
        "order_info_sub": "Remplissez ces informations puis cliquez sur le bouton vert.",
        "pay_whatsapp": "Valider et envoyer par WhatsApp",
        "order_summary": "Récapitulatif de commande",
        "thank_you": "Merci pour votre commande !",
        "order_saved": "Votre commande a bien été enregistrée.",
        "last_step": "Dernière étape : envoyez-nous votre commande par WhatsApp",
        "we_respond": "Nous vous répondrons immédiatement avec les détails de paiement.",
        "send_whatsapp": "Envoyer ma commande par WhatsApp",
        "my_orders": "Mes commandes", "no_orders": "Aucune commande pour le moment.",
        "page_not_found": "Page introuvable", "error_404": "Erreur 404",
        "back_home": "Retour à l'accueil",
        "select_options": "Sélectionner les options",
        "product_variants": "Ce produit existe en plusieurs variantes.",
        "guest_note": "Vous n'avez pas besoin de compte pour commander.",
        "contact_desc": "Une question ? Notre équipe vous répond 24h/24 et 7j/7.",
        "message_sent": "Message envoyé ! Nous vous répondrons rapidement.",
        "read_more": "En savoir plus",
        "blog_intro": "Pour en savoir plus, consultez nos articles informatifs.",
        "faq_intro": "Réponses à vos questions les plus importantes",
        "faq_sub": "Trouvez rapidement les réponses aux questions fréquemment posées.",
        "gallery": "Galerie photos",
        "photos_upload": "Ajouter jusqu'à 5 photos",
        "photos_max": "Maximum 5 photos par produit",
        "photos_current": "Photos actuelles",
        "upload": "Téléverser",
        "delete": "Supprimer",
    },
    "en": {
        "welcome": "Welcome to the Monjaroo shop",
        "hero_title": "Premium wellness products for daily health",
        "hero_text": "Discover high-quality supplements and wellness products, rigorously tested and approved.",
        "buy_now": "Shop now", "search": "Search", "search_ph": "Search for a product...",
        "login": "Sign in", "register": "Sign up", "logout": "Sign out",
        "account": "My account", "cart": "Cart", "empty_cart": "Your cart is empty.",
        "home": "Home", "meds": "Medications", "peptides": "Peptides",
        "pills": "Erection pills", "general": "General", "blog": "Blog", "contact": "Contact",
        "cgv": "Terms", "returns": "Returns", "privacy": "Privacy", "fair": "Fair questions",
        "faq": "FAQ",
        "reviews": "Reviews", "reviews_title": "What our customers say",
        "leave_review": "Leave your review", "post_review": "Post my review",
        "add_to_cart": "Add to cart", "your_cart": "Your cart",
        "checkout": "Checkout", "order_wa": "Order via WhatsApp",
        "features_home": "Trusted shop offering quality products.",
        "features_price": "Affordable prices for all.",
        "features_ship": "Free express delivery with tracking.",
        "features_support": "24/7 online support.",
        "newsletter": "Get 10% off your next order",
        "newsletter_sub": "Subscribe to our newsletter.",
        "subscribe": "Subscribe", "email_ph": "Your email",
        "about_us": "About us", "about_title": "Promoting health through quality and care",
        "about_text": "At Monjaroo.shop, we believe true health starts with trust.",
        "discover": "Discover our peptides and medications",
        "contact_us": "Contact us", "all_rights": "All rights reserved",
        "full_name": "Full name", "email": "Email", "phone": "Phone",
        "address": "Delivery address", "password": "Password", "confirm_password": "Confirm password",
        "send": "Send", "message": "Message", "total": "Total", "quantity": "Quantity",
        "welcome_back": "Welcome back!", "invalid_credentials": "Invalid credentials.",
        "email_exists": "Email already used.",
        "account_created": "Account created!",
        "passwords_dont_match": "Passwords don't match.",
        "you_are_logged": "You are logged in.",
        "order_info_title": "Your delivery information",
        "order_info_sub": "Fill in then click the green button.",
        "pay_whatsapp": "Confirm via WhatsApp",
        "order_summary": "Order summary",
        "thank_you": "Thank you!",
        "order_saved": "Your order has been recorded.",
        "last_step": "Last step: send us your order via WhatsApp",
        "we_respond": "We will respond with payment details.",
        "send_whatsapp": "Send order via WhatsApp",
        "my_orders": "My orders", "no_orders": "No orders yet.",
        "page_not_found": "Page not found", "error_404": "Error 404",
        "back_home": "Back home",
        "select_options": "Select options",
        "product_variants": "This product has several variants.",
        "guest_note": "No account needed to order.",
        "contact_desc": "A question? Our team answers 24/7.",
        "message_sent": "Message sent!",
        "read_more": "Read more",
        "blog_intro": "Read our informative articles.",
        "faq_intro": "Answers to your questions",
        "faq_sub": "Find answers to frequently asked questions.",
        "gallery": "Photo gallery",
        "photos_upload": "Add up to 5 photos",
        "photos_max": "Maximum 5 photos per product",
        "photos_current": "Current photos",
        "upload": "Upload",
        "delete": "Delete",
    },
    "nl": {
        "welcome": "Welkom bij Monjaroo",
        "hero_title": "Premium wellnessproducten",
        "hero_text": "Ontdek hoogwaardige supplementen.",
        "buy_now": "Nu kopen", "search": "Zoeken", "search_ph": "Zoek een product...",
        "login": "Inloggen", "register": "Registreren", "logout": "Uitloggen",
        "account": "Mijn account", "cart": "Winkelwagen", "empty_cart": "Winkelwagen is leeg.",
        "home": "Home", "meds": "Medicijnen", "peptides": "Peptiden",
        "pills": "Erectiepillen", "general": "Algemeen", "blog": "Blog", "contact": "Contact",
        "cgv": "Voorwaarden", "returns": "Retouren", "privacy": "Privacy", "fair": "Eerlijke vragen",
        "faq": "FAQ",
        "reviews": "Beoordelingen", "reviews_title": "Wat klanten zeggen",
        "leave_review": "Beoordeling achterlaten", "post_review": "Plaatsen",
        "add_to_cart": "Toevoegen", "your_cart": "Winkelwagen",
        "checkout": "Afrekenen", "order_wa": "Bestellen via WhatsApp",
        "features_home": "Betrouwbare winkel.",
        "features_price": "Betaalbare prijzen.",
        "features_ship": "Gratis expreslevering.",
        "features_support": "24/7 ondersteuning.",
        "newsletter": "Ontvang 10% korting",
        "newsletter_sub": "Schrijf u in voor onze nieuwsbrief.",
        "subscribe": "Inschrijven", "email_ph": "Uw e-mail",
        "about_us": "Over ons", "about_title": "Gezondheid bevorderen",
        "about_text": "Wij geloven in vertrouwen.",
        "discover": "Ontdek onze producten",
        "contact_us": "Contacteer ons", "all_rights": "Alle rechten voorbehouden",
        "full_name": "Volledige naam", "email": "E-mail", "phone": "Telefoon",
        "address": "Adres", "password": "Wachtwoord", "confirm_password": "Bevestig",
        "send": "Verzenden", "message": "Bericht", "total": "Totaal", "quantity": "Aantal",
        "welcome_back": "Welkom terug!", "invalid_credentials": "Ongeldig.",
        "email_exists": "E-mail al in gebruik.",
        "account_created": "Account aangemaakt!",
        "passwords_dont_match": "Wachtwoorden komen niet overeen.",
        "you_are_logged": "U bent ingelogd.",
        "order_info_title": "Uw gegevens",
        "order_info_sub": "Vul in en klik op de groene knop.",
        "pay_whatsapp": "Bevestigen via WhatsApp",
        "order_summary": "Overzicht",
        "thank_you": "Bedankt!",
        "order_saved": "Bestelling opgeslagen.",
        "last_step": "Laatste stap: verzend via WhatsApp",
        "we_respond": "We reageren met betalingsgegevens.",
        "send_whatsapp": "Verzenden via WhatsApp",
        "my_orders": "Mijn bestellingen", "no_orders": "Geen bestellingen.",
        "page_not_found": "Pagina niet gevonden", "error_404": "Fout 404",
        "back_home": "Terug naar home",
        "select_options": "Selecteer opties",
        "product_variants": "Meerdere varianten.",
        "guest_note": "Geen account nodig.",
        "contact_desc": "Vraag? Ons team antwoordt 24/7.",
        "message_sent": "Bericht verzonden!",
        "read_more": "Lees meer",
        "blog_intro": "Lees onze artikelen.",
        "faq_intro": "Antwoorden op uw vragen",
        "faq_sub": "Vind snel antwoorden.",
        "gallery": "Fotogalerij",
        "photos_upload": "Max 5 foto's toevoegen",
        "photos_max": "Max 5 foto's per product",
        "photos_current": "Huidige foto's",
        "upload": "Uploaden",
        "delete": "Verwijderen",
    },
    "de": {
        "welcome": "Willkommen bei Monjaroo",
        "hero_title": "Premium-Wellnessprodukte",
        "hero_text": "Entdecken Sie hochwertige Wellnessprodukte.",
        "buy_now": "Jetzt kaufen", "search": "Suchen", "search_ph": "Produkt suchen...",
        "login": "Anmelden", "register": "Registrieren", "logout": "Abmelden",
        "account": "Mein Konto", "cart": "Warenkorb", "empty_cart": "Warenkorb ist leer.",
        "home": "Startseite", "meds": "Medikamente", "peptides": "Peptide",
        "pills": "Erektionspillen", "general": "Allgemein", "blog": "Blog", "contact": "Kontakt",
        "cgv": "AGB", "returns": "Rückgabe", "privacy": "Datenschutz", "fair": "Faire Fragen",
        "faq": "FAQ",
        "reviews": "Bewertungen", "reviews_title": "Was Kunden sagen",
        "leave_review": "Bewertung abgeben", "post_review": "Veröffentlichen",
        "add_to_cart": "In den Warenkorb", "your_cart": "Warenkorb",
        "checkout": "Zur Kasse", "order_wa": "Über WhatsApp bestellen",
        "features_home": "Vertrauenswürdiger Shop.",
        "features_price": "Erschwingliche Preise.",
        "features_ship": "Kostenloser Expressversand.",
        "features_support": "24/7 Support.",
        "newsletter": "Erhalten Sie 10 % Rabatt",
        "newsletter_sub": "Abonnieren Sie unseren Newsletter.",
        "subscribe": "Abonnieren", "email_ph": "Ihre E-Mail",
        "about_us": "Über uns", "about_title": "Gesundheit durch Qualität",
        "about_text": "Wir glauben an Vertrauen.",
        "discover": "Entdecken Sie unsere Produkte",
        "contact_us": "Kontakt", "all_rights": "Alle Rechte vorbehalten",
        "full_name": "Vollständiger Name", "email": "E-Mail", "phone": "Telefon",
        "address": "Adresse", "password": "Passwort", "confirm_password": "Bestätigen",
        "send": "Senden", "message": "Nachricht", "total": "Gesamt", "quantity": "Menge",
        "welcome_back": "Willkommen zurück!", "invalid_credentials": "Ungültig.",
        "email_exists": "E-Mail bereits verwendet.",
        "account_created": "Konto erstellt!",
        "passwords_dont_match": "Passwörter stimmen nicht überein.",
        "you_are_logged": "Sie sind angemeldet.",
        "order_info_title": "Ihre Daten",
        "order_info_sub": "Ausfüllen und grüne Schaltfläche klicken.",
        "pay_whatsapp": "Bestätigen via WhatsApp",
        "order_summary": "Bestellübersicht",
        "thank_you": "Danke!",
        "order_saved": "Bestellung registriert.",
        "last_step": "Letzter Schritt: via WhatsApp senden",
        "we_respond": "Wir antworten mit Zahlungsdetails.",
        "send_whatsapp": "Über WhatsApp senden",
        "my_orders": "Meine Bestellungen", "no_orders": "Keine Bestellungen.",
        "page_not_found": "Seite nicht gefunden", "error_404": "Fehler 404",
        "back_home": "Zurück",
        "select_options": "Optionen auswählen",
        "product_variants": "Mehrere Varianten.",
        "guest_note": "Kein Konto nötig.",
        "contact_desc": "Frage? Unser Team antwortet 24/7.",
        "message_sent": "Nachricht gesendet!",
        "read_more": "Mehr lesen",
        "blog_intro": "Lesen Sie unsere Artikel.",
        "faq_intro": "Antworten auf Ihre Fragen",
        "faq_sub": "Finden Sie schnell Antworten.",
        "gallery": "Fotogalerie",
        "photos_upload": "Max 5 Fotos hochladen",
        "photos_max": "Max 5 Fotos pro Produkt",
        "photos_current": "Aktuelle Fotos",
        "upload": "Hochladen",
        "delete": "Löschen",
    },
    "it": {
        "welcome": "Benvenuto da Monjaroo",
        "hero_title": "Prodotti benessere premium",
        "hero_text": "Scopri prodotti benessere di alta qualità.",
        "buy_now": "Acquista ora", "search": "Cerca", "search_ph": "Cerca prodotto...",
        "login": "Accedi", "register": "Registrati", "logout": "Esci",
        "account": "Account", "cart": "Carrello", "empty_cart": "Carrello vuoto.",
        "home": "Home", "meds": "Farmaci", "peptides": "Peptidi",
        "pills": "Pillole", "general": "Generale", "blog": "Blog", "contact": "Contatto",
        "cgv": "Termini", "returns": "Resi", "privacy": "Privacy", "fair": "Domande eque",
        "faq": "FAQ",
        "reviews": "Recensioni", "reviews_title": "Cosa dicono i clienti",
        "leave_review": "Lascia recensione", "post_review": "Pubblica",
        "add_to_cart": "Aggiungi", "your_cart": "Carrello",
        "checkout": "Procedi", "order_wa": "Ordina via WhatsApp",
        "features_home": "Negozio affidabile.",
        "features_price": "Prezzi accessibili.",
        "features_ship": "Spedizione gratuita.",
        "features_support": "Supporto 24/7.",
        "newsletter": "10% di sconto",
        "newsletter_sub": "Iscriviti alla newsletter.",
        "subscribe": "Iscriviti", "email_ph": "Tua email",
        "about_us": "Chi siamo", "about_title": "Promuovere la salute",
        "about_text": "Crediamo nella fiducia.",
        "discover": "Scopri i prodotti",
        "contact_us": "Contattaci", "all_rights": "Tutti i diritti riservati",
        "full_name": "Nome completo", "email": "Email", "phone": "Telefono",
        "address": "Indirizzo", "password": "Password", "confirm_password": "Conferma",
        "send": "Invia", "message": "Messaggio", "total": "Totale", "quantity": "Quantità",
        "welcome_back": "Bentornato!", "invalid_credentials": "Non valido.",
        "email_exists": "Email già in uso.",
        "account_created": "Account creato!",
        "passwords_dont_match": "Password diverse.",
        "you_are_logged": "Sei connesso.",
        "order_info_title": "I tuoi dati",
        "order_info_sub": "Compila e clicca il pulsante verde.",
        "pay_whatsapp": "Conferma via WhatsApp",
        "order_summary": "Riepilogo",
        "thank_you": "Grazie!",
        "order_saved": "Ordine registrato.",
        "last_step": "Ultimo passo: invia via WhatsApp",
        "we_respond": "Risponderemo con i dettagli.",
        "send_whatsapp": "Invia via WhatsApp",
        "my_orders": "I miei ordini", "no_orders": "Nessun ordine.",
        "page_not_found": "Pagina non trovata", "error_404": "Errore 404",
        "back_home": "Torna alla home",
        "select_options": "Seleziona opzioni",
        "product_variants": "Più varianti.",
        "guest_note": "Nessun account richiesto.",
        "contact_desc": "Domanda? Il team risponde 24/7.",
        "message_sent": "Messaggio inviato!",
        "read_more": "Leggi di più",
        "blog_intro": "Leggi i nostri articoli.",
        "faq_intro": "Risposte alle tue domande",
        "faq_sub": "Trova rapidamente le risposte.",
        "gallery": "Galleria foto",
        "photos_upload": "Aggiungi fino a 5 foto",
        "photos_max": "Max 5 foto per prodotto",
        "photos_current": "Foto attuali",
        "upload": "Carica",
        "delete": "Elimina",
    },
    "es": {
        "welcome": "Bienvenido a Monjaroo",
        "hero_title": "Productos de bienestar premium",
        "hero_text": "Descubre productos de bienestar de alta calidad.",
        "buy_now": "Comprar ahora", "search": "Buscar", "search_ph": "Buscar producto...",
        "login": "Iniciar sesión", "register": "Registrarse", "logout": "Cerrar sesión",
        "account": "Mi cuenta", "cart": "Carrito", "empty_cart": "Carrito vacío.",
        "home": "Inicio", "meds": "Medicamentos", "peptides": "Péptidos",
        "pills": "Píldoras", "general": "General", "blog": "Blog", "contact": "Contacto",
        "cgv": "Términos", "returns": "Devoluciones", "privacy": "Privacidad", "fair": "Preguntas",
        "faq": "FAQ",
        "reviews": "Opiniones", "reviews_title": "Lo que dicen los clientes",
        "leave_review": "Deja tu opinión", "post_review": "Publicar",
        "add_to_cart": "Añadir al carrito", "your_cart": "Tu carrito",
        "checkout": "Finalizar", "order_wa": "Pedir por WhatsApp",
        "features_home": "Tienda de confianza.",
        "features_price": "Precios asequibles.",
        "features_ship": "Envío gratis.",
        "features_support": "Soporte 24/7.",
        "newsletter": "10% descuento",
        "newsletter_sub": "Suscríbete al boletín.",
        "subscribe": "Suscribirse", "email_ph": "Tu correo",
        "about_us": "Sobre nosotros", "about_title": "Promover la salud",
        "about_text": "Creemos en la confianza.",
        "discover": "Descubre nuestros productos",
        "contact_us": "Contáctanos", "all_rights": "Todos los derechos reservados",
        "full_name": "Nombre completo", "email": "Correo", "phone": "Teléfono",
        "address": "Dirección", "password": "Contraseña", "confirm_password": "Confirmar",
        "send": "Enviar", "message": "Mensaje", "total": "Total", "quantity": "Cantidad",
        "welcome_back": "¡Bienvenido!", "invalid_credentials": "No válido.",
        "email_exists": "Correo en uso.",
        "account_created": "¡Cuenta creada!",
        "passwords_dont_match": "Las contraseñas no coinciden.",
        "you_are_logged": "Estás conectado.",
        "order_info_title": "Tu información",
        "order_info_sub": "Rellena y haz clic en el botón verde.",
        "pay_whatsapp": "Confirmar por WhatsApp",
        "order_summary": "Resumen del pedido",
        "thank_you": "¡Gracias!",
        "order_saved": "Pedido registrado.",
        "last_step": "Último paso: envía por WhatsApp",
        "we_respond": "Te responderemos con los detalles.",
        "send_whatsapp": "Enviar por WhatsApp",
        "my_orders": "Mis pedidos", "no_orders": "Sin pedidos.",
        "page_not_found": "Página no encontrada", "error_404": "Error 404",
        "back_home": "Volver al inicio",
        "select_options": "Seleccionar opciones",
        "product_variants": "Varias variantes.",
        "guest_note": "No necesitas cuenta para pedir.",
        "contact_desc": "¿Pregunta? Nuestro equipo responde 24/7.",
        "message_sent": "¡Mensaje enviado!",
        "read_more": "Leer más",
        "blog_intro": "Lee nuestros artículos.",
        "faq_intro": "Respuestas a tus preguntas",
        "faq_sub": "Encuentra rápidamente respuestas.",
        "gallery": "Galería de fotos",
        "photos_upload": "Añadir hasta 5 fotos",
        "photos_max": "Máximo 5 fotos por producto",
        "photos_current": "Fotos actuales",
        "upload": "Subir",
        "delete": "Eliminar",
    },
}


def _(key, default=None):
    try:
        lang = getattr(g, "lang", None) or app.config["DEFAULT_LANG"]
    except Exception:
        lang = app.config["DEFAULT_LANG"]
    return T.get(lang, {}).get(key, default if default is not None else key)


# =============================================================
# DÉTECTION IP → LANGUE
# =============================================================
COUNTRY_TO_LANG = {
    "FR": "fr", "BE": "fr", "LU": "fr", "MC": "fr", "SN": "fr", "CI": "fr",
    "CM": "fr", "BF": "fr", "ML": "fr", "NE": "fr", "TG": "fr", "BJ": "fr",
    "GA": "fr", "CG": "fr", "CD": "fr", "MG": "fr", "TN": "fr", "DZ": "fr",
    "MA": "fr", "HT": "fr",
    "GB": "en", "US": "en", "CA": "en", "AU": "en", "IE": "en", "NZ": "en",
    "IN": "en", "ZA": "en", "NG": "en", "KE": "en", "SG": "en", "PH": "en",
    "NL": "nl", "SR": "nl",
    "DE": "de", "AT": "de", "CH": "de", "LI": "de",
    "IT": "it", "SM": "it", "VA": "it",
    "ES": "es", "MX": "es", "AR": "es", "CO": "es", "PE": "es", "CL": "es",
    "VE": "es", "EC": "es", "UY": "es", "PY": "es", "BO": "es", "CR": "es",
    "PA": "es", "GT": "es", "CU": "es", "DO": "es", "HN": "es", "SV": "es",
    "NI": "es", "PR": "es",
}

_ip_cache = {}


def get_client_ip():
    if request.headers.get("CF-Connecting-IP"):
        return request.headers.get("CF-Connecting-IP").strip()
    xff = request.headers.get("X-Forwarded-For", "")
    if xff:
        return xff.split(",")[0].strip()
    if request.headers.get("X-Real-IP"):
        return request.headers.get("X-Real-IP").strip()
    return (request.remote_addr or "").strip()


def detect_country_from_ip(ip):
    if not ip:
        return None
    if (ip.startswith("127.") or ip.startswith("10.") or
        ip.startswith("192.168") or ip.startswith("172.") or
        ip == "::1" or ip == "localhost"):
        return None
    if ip in _ip_cache:
        return _ip_cache[ip]
    try:
        url = f"https://ipapi.co/{ip}/country/"
        req = urllib.request.Request(url, headers={"User-Agent": "Monjaroo/1.0"})
        with urllib.request.urlopen(req, timeout=3) as r:
            code = r.read().decode().strip().upper()
            if len(code) == 2 and code.isalpha():
                _ip_cache[ip] = code
                return code
    except Exception:
        pass
    try:
        url = f"http://ip-api.com/json/{ip}?fields=status,countryCode"
        with urllib.request.urlopen(url, timeout=3) as r:
            data = _json.loads(r.read().decode())
        if data.get("status") == "success":
            code = data.get("countryCode", "").upper()
            _ip_cache[ip] = code
            return code
    except Exception:
        pass
    _ip_cache[ip] = None
    return None


def detect_language():
    if "lang" in session and session["lang"] in app.config["LANGUAGES"]:
        return session["lang"]
    cookie = request.cookies.get("lang")
    if cookie in app.config["LANGUAGES"]:
        return cookie
    try:
        ip = get_client_ip()
        country = detect_country_from_ip(ip)
        if country and country in COUNTRY_TO_LANG:
            return COUNTRY_TO_LANG[country]
    except Exception:
        pass
    accept = request.headers.get("Accept-Language", "")
    for chunk in accept.split(","):
        code = chunk.strip().split(";")[0].split("-")[0].lower()
        if code in app.config["LANGUAGES"]:
            return code
    return app.config["DEFAULT_LANG"]


# =============================================================
# BASE DE DONNÉES
# =============================================================
db = SQLAlchemy(app)


class Categorie(db.Model):
    __tablename__ = "categories"
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    ordre = db.Column(db.Integer, default=0)
    produits = db.relationship("Produit", backref="categorie", lazy=True)


class Produit(db.Model):
    __tablename__ = "produits"
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False)
    description = db.Column(db.Text, default="")
    sous_titre = db.Column(db.String(150), default="")
    prix = db.Column(db.Float, nullable=False)
    prix_max = db.Column(db.Float, default=0)
    stock = db.Column(db.Integer, default=0)
    image = db.Column(db.String(500), default="")
    categorie_id = db.Column(db.Integer, db.ForeignKey("categories.id"))
    actif = db.Column(db.Boolean, default=True)
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    photos = db.relationship("PhotoProduit", backref="produit", lazy=True,
                             cascade="all, delete-orphan",
                             order_by="PhotoProduit.ordre")

    @property
    def affichage_prix(self):
        def fmt(v):
            return f"{v:,.2f} €".replace(",", " ").replace(".", ",")
        if self.prix_max and self.prix_max > self.prix:
            return f"{fmt(self.prix)} - {fmt(self.prix_max)}"
        return fmt(self.prix)

    @property
    def toutes_photos(self):
        """Retourne toutes les photos (galerie + image principale)."""
        liste = []
        if self.image:
            liste.append(self.image)
        for p in self.photos:
            if p.chemin and p.chemin not in liste:
                liste.append(p.chemin)
        return liste


class PhotoProduit(db.Model):
    __tablename__ = "photos_produit"
    id = db.Column(db.Integer, primary_key=True)
    produit_id = db.Column(db.Integer, db.ForeignKey("produits.id"), nullable=False)
    chemin = db.Column(db.String(500), nullable=False)
    ordre = db.Column(db.Integer, default=0)
    date = db.Column(db.DateTime, default=datetime.utcnow)


class Commande(db.Model):
    __tablename__ = "commandes"
    id = db.Column(db.Integer, primary_key=True)
    reference = db.Column(db.String(20), unique=True)
    user_id = db.Column(db.Integer, db.ForeignKey("utilisateurs.id"))
    nom_client = db.Column(db.String(150))
    email = db.Column(db.String(150))
    telephone = db.Column(db.String(50))
    adresse = db.Column(db.Text)
    total = db.Column(db.Float)
    statut = db.Column(db.String(50), default="en_attente")
    note = db.Column(db.Text, default="")
    date = db.Column(db.DateTime, default=datetime.utcnow)
    lignes = db.relationship("LigneCommande", backref="commande", lazy=True,
                             cascade="all, delete-orphan")


class LigneCommande(db.Model):
    __tablename__ = "lignes_commande"
    id = db.Column(db.Integer, primary_key=True)
    commande_id = db.Column(db.Integer, db.ForeignKey("commandes.id"))
    produit_id = db.Column(db.Integer, db.ForeignKey("produits.id"))
    produit_nom = db.Column(db.String(200))
    quantite = db.Column(db.Integer)
    prix_unitaire = db.Column(db.Float)
    produit = db.relationship("Produit")


class FAQ(db.Model):
    __tablename__ = "faq"
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(300), nullable=False)
    reponse = db.Column(db.Text, nullable=False)
    ordre = db.Column(db.Integer, default=0)


class Avis(db.Model):
    __tablename__ = "avis"
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(100), default="Client")
    note = db.Column(db.Integer, default=5)
    texte = db.Column(db.Text, nullable=False)
    ordre = db.Column(db.Integer, default=0)
    valide = db.Column(db.Boolean, default=True)
    date = db.Column(db.DateTime, default=datetime.utcnow)


class Contenu(db.Model):
    __tablename__ = "contenu"
    id = db.Column(db.Integer, primary_key=True)
    cle = db.Column(db.String(100), unique=True, nullable=False)
    valeur = db.Column(db.Text, default="")


class Page(db.Model):
    __tablename__ = "pages"
    id = db.Column(db.Integer, primary_key=True)
    titre = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False)
    contenu = db.Column(db.Text, default="")
    ordre = db.Column(db.Integer, default=0)
    afficher_menu = db.Column(db.Boolean, default=True)


class Message(db.Model):
    __tablename__ = "messages"
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(150))
    email = db.Column(db.String(150))
    message = db.Column(db.Text)
    lu = db.Column(db.Boolean, default=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)


class Article(db.Model):
    __tablename__ = "articles"
    id = db.Column(db.Integer, primary_key=True)
    titre = db.Column(db.String(300), nullable=False)
    slug = db.Column(db.String(300), unique=True, nullable=False)
    categorie = db.Column(db.String(100), default="Blog")
    extrait = db.Column(db.Text, default="")
    contenu = db.Column(db.Text, default="")
    image = db.Column(db.String(500), default="")
    date = db.Column(db.DateTime, default=datetime.utcnow)


class Slide(db.Model):
    __tablename__ = "slides"
    id = db.Column(db.Integer, primary_key=True)
    image = db.Column(db.String(500), nullable=False)
    ordre = db.Column(db.Integer, default=0)


class Utilisateur(UserMixin, db.Model):
    __tablename__ = "utilisateurs"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    mot_de_passe = db.Column(db.String(300), nullable=False)
    nom = db.Column(db.String(150))
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    commandes = db.relationship("Commande", backref="utilisateur", lazy=True)

    def set_password(self, pwd):
        self.mot_de_passe = generate_password_hash(pwd)

    def check_password(self, pwd):
        return check_password_hash(self.mot_de_passe, pwd)


# =============================================================
# LOGIN
# =============================================================
login_manager = LoginManager(app)
login_manager.login_view = "connexion"


class Admin(UserMixin):
    def __init__(self):
        self.id = "admin"
        self.username = app.config["ADMIN_USERNAME"]
        self.email = app.config["ADMIN_EMAIL"]

    def get_id(self):
        return "admin"


@login_manager.user_loader
def load_user(user_id):
    if user_id == "admin":
        return Admin()
    try:
        return Utilisateur.query.get(int(user_id))
    except (ValueError, TypeError):
        return None


# =============================================================
# HELPERS
# =============================================================
def slugify(txt):
    txt = txt.lower().strip()
    txt = re.sub(r"[^a-z0-9]+", "-", txt)
    return txt.strip("-") or uuid.uuid4().hex[:8]


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXT


def save_upload(file):
    if not file or not file.filename:
        return None
    if not allowed_file(file.filename):
        return None
    ext = file.filename.rsplit(".", 1)[1].lower()
    name = f"{uuid.uuid4().hex}.{ext}"
    path = os.path.join(app.config["UPLOAD_FOLDER"], name)
    file.save(path)
    return f"/static/uploads/{name}"


def get_panier():
    return session.setdefault("panier", {})


def total_panier():
    panier = get_panier()
    if not panier:
        return 0.0
    ids = [int(i) for i in panier.keys()]
    produits = Produit.query.filter(Produit.id.in_(ids)).all()
    return sum(p.prix * panier[str(p.id)] for p in produits)


def taille_panier():
    return sum(get_panier().values())


def get_contenu(cle, defaut=""):
    c = Contenu.query.filter_by(cle=cle).first()
    return c.valeur if c and c.valeur else defaut


def wa_url(msg=None):
    num = re.sub(r"\D", "", app.config["WHATSAPP_NUMBER"])
    text = msg or app.config["WHATSAPP_MESSAGE"]
    return f"https://wa.me/{num}?text={quote(text)}"


def nouvelle_reference():
    return "MJ-" + datetime.utcnow().strftime("%y%m%d") + "-" + uuid.uuid4().hex[:6].upper()


@app.before_request
def set_language():
    g.lang = detect_language()


def _admin_only():
    try:
        return (current_user.is_authenticated
                and getattr(current_user, "id", None) == "admin")
    except Exception:
        return False


@app.template_filter("eur")
def eur(value):
    try:
        return f"{value:,.2f} €".replace(",", " ").replace(".", ",")
    except Exception:
        return value


@app.template_filter("datefr")
def datefr(value):
    return value.strftime("%d/%m/%Y") if value else ""


@app.template_filter("icon")
def icon(name, cls=""):
    from markupsafe import Markup
    svg = ICONS.get(name, "")
    if cls:
        return Markup(svg.replace("<svg ", f'<svg class="{cls}" ', 1))
    return Markup(svg)


app.jinja_env.globals["total_panier"] = total_panier
app.jinja_env.globals["taille_panier"] = taille_panier
app.jinja_env.globals["get_contenu"] = get_contenu
app.jinja_env.globals["wa_url"] = wa_url
app.jinja_env.globals["ICONS"] = ICONS
app.jinja_env.globals["_"] = _
app.jinja_env.globals["admin_only"] = _admin_only
app.jinja_env.globals["MAX_PHOTOS"] = MAX_PHOTOS_PAR_PRODUIT
# =============================================================
# CSS RESPONSIVE + STYLES GALERIE/CARROUSEL
# =============================================================
CSS = """
:root{
  --vert:#0d5e5e;--vert-clair:#1a7d7d;--violet:#a855f7;--violet-fonce:#8b3ee0;
  --jaune:#f5d547;--bg:#ffffff;--bg-alt:#f7f7f9;--fg:#1a1a1a;--muted:#6b6b6b;--border:#e5e5e5;
  --radius:12px;--radius-sm:6px;--transition:.2s;
}
*{box-sizing:border-box;-webkit-tap-highlight-color:transparent}
html{-webkit-text-size-adjust:100%;scroll-behavior:smooth}
body{margin:0;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;
  background:var(--bg);color:var(--fg);line-height:1.55;font-size:15px;overflow-x:hidden}
a{color:inherit;text-decoration:none;transition:opacity var(--transition)}
a:hover{opacity:.85}
img{max-width:100%;display:block;height:auto}
svg.ico{width:22px;height:22px;display:inline-block;vertical-align:middle;flex-shrink:0}
button{font-family:inherit}

/* TOPBAR */
.topbar{background:#f5f5f5;color:#333;font-size:13px;padding:8px 24px;
  display:flex;justify-content:space-between;align-items:center;
  border-bottom:1px solid var(--border);position:relative;z-index:1000}
.topbar .left,.topbar .right{display:flex;align-items:center;gap:10px;flex-wrap:wrap}
.lang-selector{position:relative;display:inline-block}
.lang-selector .btn-lang{display:flex;align-items:center;gap:6px;background:transparent;
  border:0;cursor:pointer;font-size:13px;color:#333;padding:6px 10px;border-radius:var(--radius-sm)}
.lang-selector .btn-lang:hover{background:#e8e8e8}
.lang-selector .btn-lang svg{width:16px;height:16px;pointer-events:none}
.lang-selector .btn-lang > *{pointer-events:none}
.lang-selector .menu{position:absolute;top:calc(100% + 4px);left:0;background:#fff;
  border:1px solid var(--border);border-radius:8px;box-shadow:0 8px 24px rgba(0,0,0,.15);
  min-width:210px;padding:6px 0;display:none;z-index:99999}
.lang-selector.open .menu{display:block}
.lang-selector .menu a{display:flex;align-items:center;gap:10px;padding:10px 16px;font-size:13px;color:#111}
.lang-selector .menu a:hover{background:#f7f7f9}
.lang-selector .menu a.active{background:#f3e8ff;color:var(--violet);font-weight:600}
.lang-selector .flag{font-size:16px}
.country-block{display:flex;align-items:center;gap:8px;font-weight:500;color:#222}
.country-block .flag{font-size:16px}
.country-block .wa-mini{display:inline-flex;align-items:center;color:#25d366;margin-left:4px}
.country-block .wa-mini svg{width:18px;height:18px}

/* HEADER */
.header{background:#fff;padding:16px 24px;display:flex;align-items:center;
  gap:24px;border-bottom:1px solid var(--border);position:relative;z-index:100}
.header .logo{font-size:24px;font-weight:800;color:var(--vert);white-space:nowrap}
.header .logo span{color:var(--violet)}
.search{flex:1;max-width:520px;display:flex;background:#f2f2f2;
  border-radius:30px;overflow:hidden;padding:4px;align-items:center}
.search input{flex:1;border:0;background:transparent;padding:10px 18px;font-size:14px;outline:none;min-width:0}
.search button{background:var(--violet);color:#fff;border:0;padding:8px 18px;
  border-radius:30px;cursor:pointer;font-weight:600;display:flex;align-items:center;gap:6px;
  font-family:inherit;white-space:nowrap}
.search button svg{width:18px;height:18px;pointer-events:none}
.header-right{margin-left:auto;display:flex;align-items:center;gap:14px;font-size:14px}
.header-right a,.header-right button{display:flex;align-items:center;gap:6px;
  cursor:pointer;background:none;border:0;font-family:inherit;color:inherit;font-size:inherit}
.header-right .cart-btn{background:var(--violet);color:#fff;padding:10px 14px;
  border-radius:30px;font-weight:600;white-space:nowrap}
.header-right .cart-btn svg{width:20px;height:20px;stroke:#fff;pointer-events:none}
.header-right .admin-btn{background:var(--vert);color:#fff;padding:10px 14px;
  border-radius:30px;font-weight:600}
.burger{display:none;cursor:pointer;color:var(--vert);padding:8px;background:none;border:0}

/* NAV */
.nav{padding:0 24px;display:flex;gap:26px;font-size:14px;font-weight:500;
  border-bottom:1px solid var(--border);background:#fff;flex-wrap:wrap;
  position:relative;z-index:99;align-items:center}
.nav>a,.nav .dropdown>span{padding:14px 0;color:var(--fg);
  border-bottom:3px solid transparent;cursor:pointer;display:inline-flex;
  align-items:center;gap:6px;transition:all var(--transition)}
.nav>a:hover,.nav>a.active,.nav .dropdown:hover>span{color:var(--violet);border-bottom-color:var(--violet)}
.dropdown{position:relative;display:inline-block}
.dropdown>span svg{width:14px;height:14px;pointer-events:none;transition:transform var(--transition)}
.dropdown:hover>span svg{transform:rotate(180deg)}
.dropdown-menu{position:absolute;top:100%;left:0;background:#fff;border:1px solid var(--border);
  border-radius:8px;box-shadow:0 8px 24px rgba(0,0,0,.1);min-width:280px;padding:8px 0;
  display:none;z-index:200}
.dropdown:hover .dropdown-menu{display:block}
.dropdown-menu a{display:block;padding:11px 20px;color:#111;font-size:14px;white-space:nowrap}
.dropdown-menu a:hover{background:#f7f7f9;color:var(--violet);opacity:1}

/* HERO */
.hero{position:relative;color:#fff;padding:72px 24px;overflow:hidden;
  min-height:480px;display:flex;align-items:center}
.hero-bg{position:absolute;inset:0;z-index:0}
.hero-slide{position:absolute;inset:0;background-size:cover;background-position:center;
  opacity:0;transition:opacity 1.5s ease-in-out}
.hero-slide.active{opacity:1}
.hero-bg::after{content:"";position:absolute;inset:0;z-index:1;
  background:linear-gradient(90deg,rgba(0,0,0,.75) 0%,rgba(0,0,0,.4) 60%,rgba(0,0,0,.1) 100%)}
.hero-inner{position:relative;z-index:2;max-width:640px;margin:0 auto;width:100%}
.hero-badge{display:inline-flex;align-items:center;gap:10px;font-size:14px;
  margin-bottom:18px;opacity:.95}
.hero-badge .dot{width:32px;height:32px;border-radius:50%;background:var(--violet);
  display:flex;align-items:center;justify-content:center;color:#fff;flex-shrink:0}
.hero-badge .dot svg{width:18px;height:18px}
.hero h1{font-size:42px;line-height:1.15;font-weight:800;margin:0 0 18px;color:#fff}
.hero p{font-size:16px;margin:0 0 24px;opacity:.92;max-width:560px}
.hero .btn{background:var(--violet);color:#fff;padding:14px 28px;border-radius:8px;
  font-weight:700;display:inline-block;font-size:15px}
.hero-dots{position:absolute;bottom:20px;left:50%;transform:translateX(-50%);
  display:flex;gap:8px;z-index:3}
.hero-dots span{width:10px;height:10px;border-radius:50%;background:rgba(255,255,255,.5);
  cursor:pointer;transition:all .3s}
.hero-dots span.active{background:#fff;width:26px;border-radius:5px}

/* FEATURES */
.features{background:var(--bg-alt);padding:28px 24px;display:grid;
  grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:16px;max-width:1200px;margin:0 auto}
.feature{background:#fff;border-radius:var(--radius);padding:20px;display:flex;
  gap:14px;align-items:flex-start;box-shadow:0 2px 8px rgba(0,0,0,.04)}
.feature .ico{color:var(--vert);flex-shrink:0;margin-top:2px}
.feature .ico svg{width:26px;height:26px}
.feature p{margin:0;font-size:14px;color:#333}

/* SECTIONS */
.section{max-width:1200px;margin:0 auto;padding:56px 24px}
.section-sm{max-width:1200px;margin:0 auto;padding:32px 24px}
.about{display:grid;grid-template-columns:1fr 1fr;gap:48px;align-items:center}
.about img{border-radius:14px;width:100%}
.about .label{color:var(--violet);font-weight:600;font-size:13px;margin-bottom:10px;text-transform:uppercase;letter-spacing:.5px}
.about h2{font-size:28px;margin:0 0 18px;color:#111;font-weight:800;line-height:1.25}
.about p{color:#555;font-size:15px}

.violet-section{background:linear-gradient(135deg,#7b2f9e 0%,#a855f7 100%);
  color:#fff;padding:56px 24px}
.violet-inner{max-width:1200px;margin:0 auto}
.violet-section h2{font-size:30px;margin:0 0 28px;color:#fff;font-weight:800}
.violet-section h3{font-size:20px;margin:26px 0 10px;color:#fff;
  border-bottom:2px solid rgba(255,255,255,.4);display:inline-block;padding-bottom:4px}
.violet-section p{font-size:15px;color:#f0e6f7;margin:0 0 10px;max-width:640px}

/* AVIS */
.avis-label{color:var(--violet);font-weight:600;font-size:13px;margin-bottom:6px;text-transform:uppercase;letter-spacing:.5px}
.avis-title{font-size:28px;font-weight:800;margin:0 0 20px;color:#111}
.avis-stats{display:flex;gap:28px;align-items:center;margin-bottom:28px;
  padding:18px 22px;background:var(--bg-alt);border-radius:var(--radius);flex-wrap:wrap}
.avis-stats .big{font-size:38px;font-weight:800;color:var(--vert);line-height:1}
.avis-stats .stars{display:flex;gap:2px}
.avis-stats .stars svg{width:20px;height:20px}
.avis-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:20px}
.avis-card{border:1px solid var(--border);border-radius:var(--radius);padding:22px;
  background:#fff;position:relative}
.avis-card .quote{color:#eee;font-size:42px;line-height:1;font-family:Georgia,serif;
  position:absolute;top:12px;right:16px}
.avis-stars{display:flex;gap:2px;margin-bottom:12px}
.avis-stars svg{width:18px;height:18px}
.avis-nom{font-weight:700;font-size:15px;margin-bottom:2px}
.avis-role{color:var(--violet);font-size:12px;margin-bottom:10px}
.avis-texte{color:#555;font-size:14px;line-height:1.6}
.avis-footer{margin-top:8px;font-size:12px;color:#999}
.avis-form{max-width:600px;margin:36px auto 0;background:#fff;
  border:1px solid var(--border);border-radius:var(--radius);padding:26px}
.avis-form h3{margin:0 0 6px;color:var(--vert);font-size:20px}
.avis-form p.sub{color:#666;margin:0 0 18px;font-size:14px}
.avis-form .stars-input{display:flex;gap:6px;margin-bottom:14px}
.avis-form .stars-input label{cursor:pointer;font-size:0}
.avis-form .stars-input svg{width:30px;height:30px;fill:#ddd}
.avis-form .stars-input label:hover svg,.avis-form .stars-input label:hover ~ label svg,
.avis-form .stars-input input:checked ~ label svg{fill:#f5b301}

/* ============================================================
   GALERIE PHOTO PRODUIT (page publique)
   ============================================================ */
.product-page{display:grid;grid-template-columns:1fr 1fr;gap:36px;align-items:start}

/* Carrousel principal */
.gallery-wrap{position:sticky;top:20px}
.gallery-main{
  position:relative;
  aspect-ratio:1/1;
  background:#fff;
  border:1px solid var(--border);
  border-radius:var(--radius);
  overflow:hidden;
  box-shadow:0 4px 16px rgba(0,0,0,.06);
}
.gallery-main .slide{
  position:absolute;
  inset:0;
  opacity:0;
  transition:opacity .6s ease-in-out;
  background-size:cover;
  background-position:center;
  background-repeat:no-repeat;
}
.gallery-main .slide.active{opacity:1}

/* Compteur en haut à droite */
.gallery-main .counter{
  position:absolute;
  top:12px;
  right:12px;
  background:rgba(0,0,0,.55);
  color:#fff;
  font-size:12px;
  padding:4px 10px;
  border-radius:20px;
  font-weight:600;
  z-index:5;
  backdrop-filter:blur(4px);
}

/* Flèches de navigation */
.gallery-main .nav-btn{
  position:absolute;
  top:50%;
  transform:translateY(-50%);
  width:38px;
  height:38px;
  border-radius:50%;
  background:rgba(255,255,255,.9);
  border:0;
  cursor:pointer;
  display:flex;
  align-items:center;
  justify-content:center;
  box-shadow:0 2px 8px rgba(0,0,0,.15);
  z-index:5;
  color:#111;
  transition:background var(--transition);
}
.gallery-main .nav-btn:hover{background:#fff}
.gallery-main .nav-btn.prev{left:12px}
.gallery-main .nav-btn.next{right:12px}
.gallery-main .nav-btn svg{width:18px;height:18px}

/* Points indicateurs */
.gallery-main .dots{
  position:absolute;
  bottom:12px;
  left:50%;
  transform:translateX(-50%);
  display:flex;
  gap:6px;
  z-index:5;
}
.gallery-main .dots span{
  width:8px;
  height:8px;
  border-radius:50%;
  background:rgba(255,255,255,.6);
  cursor:pointer;
  transition:all .3s;
}
.gallery-main .dots span.active{
  background:#fff;
  width:24px;
  border-radius:4px;
}

/* Miniatures */
.gallery-thumbs{
  display:flex;
  gap:10px;
  margin-top:14px;
  flex-wrap:wrap;
  justify-content:center;
}
.gallery-thumb{
  width:70px;
  height:70px;
  border-radius:8px;
  border:2px solid transparent;
  background-size:cover;
  background-position:center;
  cursor:pointer;
  transition:all var(--transition);
  background-color:#f7f7f9;
}
.gallery-thumb:hover{border-color:var(--violet)}
.gallery-thumb.active{border-color:var(--violet);box-shadow:0 0 0 2px rgba(168,85,247,.2)}

/* ============================================================
   ADMIN — FORMULAIRE UPLOAD PHOTOS
   ============================================================ */
.photo-upload-section{
  background:#f7f7f9;
  border:1px dashed var(--border);
  border-radius:var(--radius);
  padding:20px;
  margin:20px 0;
}
.photo-upload-section h3{
  margin:0 0 8px;
  color:var(--vert);
  font-size:16px;
  display:flex;
  align-items:center;
  gap:8px;
}
.photo-upload-section .hint{
  color:#777;
  font-size:13px;
  margin:0 0 14px;
}
.photo-upload-section input[type=file]{
  width:100%;
  padding:12px;
  background:#fff;
  border:1px solid var(--border);
  border-radius:var(--radius-sm);
  margin-bottom:12px;
  font-size:13px;
}
.photo-upload-section button{
  background:var(--violet);
  color:#fff;
  border:0;
  padding:10px 22px;
  border-radius:var(--radius-sm);
  font-weight:600;
  cursor:pointer;
  font-family:inherit;
}
.photo-upload-section button:hover{background:var(--violet-fonce)}

.photo-grid{
  display:grid;
  grid-template-columns:repeat(auto-fill,minmax(120px,1fr));
  gap:12px;
  margin-top:14px;
}
.photo-item{
  position:relative;
  aspect-ratio:1/1;
  border-radius:8px;
  overflow:hidden;
  background:#fff;
  border:1px solid var(--border);
}
.photo-item img{width:100%;height:100%;object-fit:cover}
.photo-item .del-btn{
  position:absolute;
  top:6px;
  right:6px;
  width:26px;
  height:26px;
  border-radius:50%;
  background:rgba(239,68,68,.95);
  color:#fff;
  border:0;
  cursor:pointer;
  display:flex;
  align-items:center;
  justify-content:center;
  font-size:16px;
  line-height:1;
  font-weight:700;
  padding:0;
}
.photo-item .del-btn:hover{background:#dc2626}

.photo-counter{
  display:inline-block;
  background:var(--violet);
  color:#fff;
  font-size:12px;
  padding:3px 10px;
  border-radius:12px;
  font-weight:600;
  margin-left:8px;
}

/* FLOAT BTNS */
.float-btns{position:fixed;bottom:20px;right:20px;z-index:99999;
  display:flex;flex-direction:column;gap:10px;align-items:flex-end;pointer-events:none}
.float-btns > *{pointer-events:auto}
.wa-cta{display:flex;align-items:center;gap:8px;background:#fff;color:#111;
  padding:9px 16px;border-radius:30px;box-shadow:0 4px 16px rgba(0,0,0,.15);
  font-size:13px;font-weight:500;cursor:pointer}
.wa-btn{width:54px;height:54px;border-radius:50%;background:#25d366;
  display:flex;align-items:center;justify-content:center;color:#fff;
  box-shadow:0 4px 16px rgba(37,211,102,.4);transition:transform var(--transition);cursor:pointer}
.wa-btn:hover{transform:scale(1.08)}
.wa-btn svg{width:30px;height:30px;fill:#fff;pointer-events:none}
.cart-float{width:54px;height:54px;border-radius:50%;background:var(--violet);
  display:flex;align-items:center;justify-content:center;color:#fff;
  box-shadow:0 4px 16px rgba(168,85,247,.4);position:relative;cursor:pointer;
  border:0;padding:0;pointer-events:auto}
.cart-float svg{width:26px;height:26px;stroke:#fff;pointer-events:none}
.cart-float .badge{position:absolute;top:-4px;right:-4px;background:#ef4444;color:#fff;
  font-size:11px;padding:2px 6px;border-radius:10px;font-weight:700;pointer-events:none}

/* CART DRAWER */
.cart-overlay{position:fixed;inset:0;background:rgba(0,0,0,.4);opacity:0;
  pointer-events:none;transition:opacity .25s;z-index:100000}
.cart-overlay.open{opacity:1;pointer-events:auto}
.cart-drawer{position:fixed;top:0;right:0;height:100%;width:400px;max-width:92vw;
  background:#fff;box-shadow:-4px 0 20px rgba(0,0,0,.15);z-index:100001;
  transform:translateX(100%);transition:transform .3s;display:flex;flex-direction:column}
.cart-drawer.open{transform:translateX(0)}
.cart-head{padding:18px 22px;border-bottom:1px solid var(--border);
  display:flex;justify-content:space-between;align-items:center}
.cart-head h3{margin:0;font-size:17px}
.cart-close{background:none;border:0;cursor:pointer;color:#777;padding:6px;
  border-radius:var(--radius-sm);display:flex;align-items:center;justify-content:center}
.cart-close:hover{background:#f0f0f0;color:var(--violet)}
.cart-close svg{width:22px;height:22px;pointer-events:none}
.cart-body{flex:1;overflow-y:auto;padding:14px 22px}
.cart-item{display:flex;gap:12px;padding:12px 0;border-bottom:1px solid var(--border)}
.cart-item img{width:64px;height:64px;object-fit:cover;border-radius:8px;background:#f2f2f2}
.cart-item-info{flex:1;min-width:0}
.cart-item-info h4{margin:0 0 4px;font-size:14px;overflow:hidden;text-overflow:ellipsis}
.cart-item-info .prix{color:var(--violet);font-weight:700;font-size:13px}
.cart-item-qte{display:flex;align-items:center;gap:6px;margin-top:6px}
.cart-item-qte input{width:50px;padding:4px;text-align:center;
  border:1px solid var(--border);border-radius:var(--radius-sm)}
.cart-item-remove{background:none;border:0;color:#c33;cursor:pointer;font-size:12px}
.cart-foot{padding:18px 22px;border-top:1px solid var(--border);background:#fafafa}
.cart-total{display:flex;justify-content:space-between;font-size:16px;font-weight:700;
  color:var(--vert);margin-bottom:12px}
.cart-foot .btn-cart{display:block;text-align:center;background:var(--violet);color:#fff;
  padding:12px;border-radius:8px;font-weight:700;margin-bottom:8px;cursor:pointer}
.cart-empty{text-align:center;color:var(--muted);padding:40px 0}

/* GRILLE PRODUITS */
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:22px}
.card{background:#fff;border:1px solid var(--border);border-radius:var(--radius);
  overflow:hidden;display:flex;flex-direction:column;transition:box-shadow var(--transition)}
.card:hover{box-shadow:0 8px 24px rgba(0,0,0,.08)}
.card-img{aspect-ratio:1/1;background:var(--bg-alt);display:flex;
  align-items:center;justify-content:center;overflow:hidden}
.card-img img{width:100%;height:100%;object-fit:cover}
.card-body{padding:14px;display:flex;flex-direction:column;gap:8px;flex:1}
.card-cat{font-size:11px;text-transform:lowercase;color:var(--violet);
  background:#f3e8ff;display:inline-block;padding:3px 10px;border-radius:12px;
  align-self:flex-start;font-weight:600}
.card-title{font-size:15px;font-weight:600;color:#111;margin:0;line-height:1.35}
.card-price{font-size:17px;font-weight:700;color:var(--violet);margin:4px 0}
.card-form{display:flex;gap:6px;margin-top:auto}
.card-form input[type=number]{width:54px;padding:8px;border:1px solid var(--border);
  border-radius:var(--radius-sm);text-align:center;font-size:14px}
.card-form button{flex:1;background:var(--violet);color:#fff;border:0;padding:10px;
  border-radius:var(--radius-sm);font-weight:600;cursor:pointer;font-size:13px}
.card-form button:hover{background:var(--violet-fonce)}
.card-form .btn-options{background:#fff;color:var(--violet);border:2px solid var(--violet)}
.card-note{font-size:12px;color:#8a8a8a;font-style:italic;margin-top:4px}

/* BLOG */
.blog-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:22px}
.blog-card{border:1px solid var(--border);border-radius:var(--radius);
  overflow:hidden;background:#fff;display:flex;flex-direction:column}
.blog-card img{aspect-ratio:16/9;object-fit:cover;width:100%}
.blog-card-body{padding:18px;flex:1;display:flex;flex-direction:column}
.blog-card .cat-label{color:var(--violet);font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:.5px;margin-bottom:6px}
.blog-card .date{color:#999;font-size:12px;margin-bottom:6px}
.blog-card h3{margin:0 0 10px;font-size:17px;color:#111;line-height:1.35}
.blog-card p{color:#555;font-size:14px;margin:0 0 12px;flex:1}
.blog-card a.read{color:var(--violet);font-weight:600;font-size:14px;margin-top:auto}

/* FAQ */
details{background:#fff;border:1px solid var(--border);border-radius:10px;margin-bottom:10px}
details summary{cursor:pointer;padding:16px 20px;font-weight:600;color:#111;
  list-style:none;display:flex;justify-content:space-between;align-items:center;font-size:15px}
details summary::after{content:"+";font-size:20px;color:var(--violet);transition:transform var(--transition)}
details[open] summary::after{transform:rotate(45deg)}
details p{margin:0;padding:0 20px 16px;color:#555;font-size:14px;line-height:1.7}

/* LEGAL */
.legal h1{margin-bottom:8px}
.legal h2{color:var(--vert);font-size:19px;margin:28px 0 10px}
.legal h3{color:#111;font-size:16px;margin:20px 0 8px}
.legal p,.legal li{color:#444;font-size:14px;line-height:1.75}
.legal ul{padding-left:22px}

/* NEWSLETTER */
.newsletter{background:var(--vert);color:#fff;padding:48px 24px;text-align:center}
.newsletter h2{color:#fff;font-size:24px;margin:0 0 8px}
.newsletter p{color:#c9dede;margin-bottom:22px;font-size:14px}
.newsletter form{display:flex;gap:10px;max-width:520px;margin:0 auto 14px;flex-wrap:wrap;justify-content:center}
.newsletter input{flex:1;min-width:220px;padding:12px 18px;border:0;
  border-radius:30px;font-size:14px}
.newsletter button{background:var(--violet);color:#fff;border:0;padding:12px 26px;
  border-radius:30px;font-weight:700;cursor:pointer}

/* FOOTER */
footer{background:#0a2e2e;color:#b8c9c9;padding:48px 24px 22px;font-size:13px}
.footer-grid{max-width:1200px;margin:0 auto;display:grid;
  grid-template-columns:2fr 1fr 1fr 1.5fr;gap:32px;margin-bottom:32px}
.footer-grid h4{color:#fff;font-size:15px;margin:0 0 12px}
.footer-grid ul{list-style:none;padding:0;margin:0;display:flex;flex-direction:column;gap:8px}
.footer-grid a{color:#b8c9c9;display:inline-flex;align-items:center;gap:6px}
.footer-grid a:hover{color:#fff}
.footer-grid a svg{width:14px;height:14px}
.footer-copy{border-top:1px solid #1a4444;padding-top:16px;text-align:center;font-size:12px}

/* FLASH */
.flash{max-width:1200px;margin:14px auto 0;padding:0 24px}
.flash-success{background:#e6f4ea;color:#1e6b3a;padding:12px;border-radius:var(--radius-sm);margin-bottom:8px}
.flash-error{background:#fdecea;color:#a32115;padding:12px;border-radius:var(--radius-sm);margin-bottom:8px}
.flash-info{background:#e8f0ff;color:#1e3a8a;padding:12px;border-radius:var(--radius-sm);margin-bottom:8px}

/* FORMULAIRES */
.form label{display:block;margin-bottom:14px;font-size:14px;font-weight:500}
.form input,.form textarea,.form select{width:100%;padding:10px 12px;
  border:1px solid var(--border);border-radius:var(--radius-sm);margin-top:4px;
  font-size:14px;font-family:inherit;background:#fff}
.form button{background:var(--violet);color:#fff;border:0;padding:11px 22px;
  border-radius:var(--radius-sm);font-weight:600;cursor:pointer;font-family:inherit}

/* PWD EYE */
.pwd-wrap{position:relative;display:block;margin-top:4px}
.pwd-wrap input{padding-right:56px;width:100%;margin-top:0}
.pwd-toggle{position:absolute;right:8px;top:50%;transform:translateY(-50%);
  background:var(--violet);border:0;cursor:pointer;color:#fff;
  padding:8px;display:flex;align-items:center;justify-content:center;
  border-radius:var(--radius-sm);z-index:50;font-family:inherit;min-width:36px;min-height:36px}
.pwd-toggle:hover{background:var(--violet-fonce)}
.pwd-toggle svg{width:18px;height:18px;pointer-events:none;stroke:#fff;fill:none}

/* TABLEAUX */
table{width:100%;border-collapse:collapse;margin-top:14px;font-size:14px}
th,td{padding:10px;border-bottom:1px solid var(--border);text-align:left}
th{background:var(--bg-alt);color:#111;font-weight:600}
button.btn{background:var(--violet);color:#fff;border:0;padding:8px 14px;
  border-radius:var(--radius-sm);cursor:pointer;font-weight:600;font-family:inherit}
.btn-link{display:inline-block;background:var(--violet);color:#fff;padding:10px 18px;
  border-radius:var(--radius-sm);margin:8px 0;font-weight:600;cursor:pointer}

/* BADGES */
.badge-status{display:inline-block;padding:3px 10px;border-radius:12px;font-size:12px;font-weight:600}
.badge-en_attente{background:#fef3c7;color:#92400e}
.badge-en_cours{background:#dbeafe;color:#1e40af}
.badge-expediee{background:#e0e7ff;color:#3730a3}
.badge-livree{background:#d1fae5;color:#065f46}
.badge-annulee{background:#fee2e2;color:#991b1b}

/* ERROR */
.error-page{text-align:center;padding:100px 24px}
.error-page h1{font-size:80px;color:var(--violet);margin:0}
.error-page p{color:var(--muted);font-size:18px;margin:8px 0 22px}

/* ADMIN */
.admin-wrap{display:flex;min-height:100vh;background:#f0f2f5}
.admin-side{width:230px;background:var(--vert);color:#fff;padding:22px 0;flex-shrink:0}
.admin-side h2{font-size:15px;padding:0 20px;margin:0 0 18px;color:#fff;letter-spacing:1px}
.admin-side a{display:block;padding:11px 20px;color:#c9dede;font-size:14px;
  border-left:3px solid transparent;transition:background var(--transition)}
.admin-side a:hover{background:#0a2e2e;color:#fff}
.admin-side a.active{background:#0a2e2e;color:#fff;border-left-color:var(--jaune)}
.admin-side .sep{border-top:1px solid #1a4444;margin:12px 0}
.admin-main{flex:1;padding:28px;min-width:0}
.admin-main h1{margin:0 0 22px;color:#111;font-size:24px}
.stat-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));
  gap:14px;margin-bottom:28px}
.stat-card{background:#fff;padding:18px;border-radius:var(--radius);
  box-shadow:0 2px 8px rgba(0,0,0,.04)}
.stat-card .label{color:#888;font-size:13px;margin-bottom:6px}
.stat-card .value{font-size:28px;font-weight:800}
.stat-card.vert .value{color:var(--vert)}
.stat-card.violet .value{color:var(--violet)}
.stat-card.orange .value{color:#d97706}
.stat-card.blue .value{color:#2563eb}
.stat-card.red .value{color:#dc2626}
.stat-card.green .value{color:#059669}

/* CHECKOUT */
.checkout-btn{display:flex;align-items:center;justify-content:center;gap:10px;
  background:#25d366;color:#fff;padding:16px 24px;border-radius:10px;font-weight:700;
  font-size:16px;cursor:pointer;border:0;font-family:inherit;width:100%;
  margin-top:16px;transition:background var(--transition)}
.checkout-btn:hover{background:#1eb955}
.checkout-btn svg{width:24px;height:24px;fill:#fff;pointer-events:none}

/* ============================================================
   RESPONSIVE TABLETTE
   ============================================================ */
@media(max-width:1024px){
  .hero h1{font-size:36px}
  .hero{min-height:420px;padding:60px 20px}
  .section{padding:48px 20px}
  .about{gap:36px}
  .about h2{font-size:24px}
  .violet-section h2{font-size:26px}
  .grid{grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:18px}
  .footer-grid{grid-template-columns:1.5fr 1fr 1fr 1.2fr;gap:24px}
  .product-page{gap:24px}
}

/* ============================================================
   RESPONSIVE MOBILE
   ============================================================ */
@media(max-width:768px){
  .topbar{padding:6px 12px;font-size:12px;flex-wrap:wrap;gap:6px}
  .topbar .left,.topbar .right{gap:6px}
  .country-block span:not(.flag){display:none}
  .country-block{font-size:12px}

  .header{padding:12px 14px;flex-wrap:wrap;gap:10px}
  .header .logo{font-size:20px}
  .search{order:3;width:100%;max-width:none;padding:3px}
  .search input{padding:8px 14px;font-size:13px}
  .search button{padding:7px 14px;font-size:13px}
  .header-right{gap:10px;margin-left:0;width:100%;justify-content:space-between}
  .header-right .cart-btn{padding:8px 12px;font-size:13px}
  .header-right .cart-btn svg{width:18px;height:18px}
  .header-right a:not(.cart-btn):not(.admin-btn){font-size:13px}
  .burger{display:flex;order:4}

  .nav{display:none;flex-direction:column;gap:0;padding:0;border-bottom:1px solid var(--border)}
  .nav.open{display:flex}
  .nav>a,.nav .dropdown{display:block;width:100%}
  .nav>a,.nav .dropdown>span{padding:13px 18px;border-bottom:1px solid var(--border);
    width:100%;justify-content:space-between}
  .nav>a.active,.nav .dropdown:hover>span{border-bottom-color:var(--border);
    border-left:3px solid var(--violet);padding-left:15px}
  .dropdown-menu{position:static;box-shadow:none;border:0;border-radius:0;
    display:block;padding:0;background:#fafafa}
  .dropdown-menu a{padding:11px 32px;border-bottom:1px solid var(--border);font-size:13px}

  .hero{min-height:380px;padding:50px 18px}
  .hero h1{font-size:28px;line-height:1.2}
  .hero p{font-size:14px}
  .hero .btn{padding:12px 22px;font-size:14px}
  .hero-badge{font-size:12px}
  .hero-badge .dot{width:26px;height:26px}
  .hero-badge .dot svg{width:14px;height:14px}

  .features{padding:20px 14px;grid-template-columns:1fr 1fr;gap:10px}
  .feature{padding:14px;gap:10px}
  .feature .ico svg{width:22px;height:22px}
  .feature p{font-size:13px}

  .section{padding:36px 16px}
  .section-sm{padding:24px 16px}
  .about{grid-template-columns:1fr;gap:24px}
  .about h2{font-size:22px}
  .about .label{font-size:12px}
  .violet-section{padding:36px 18px}
  .violet-section h2{font-size:22px;margin-bottom:20px}
  .violet-section h3{font-size:17px;margin:20px 0 8px}
  .violet-section p{font-size:14px}

  .avis-title{font-size:22px}
  .avis-stats{gap:16px;padding:14px 16px;margin-bottom:20px}
  .avis-stats .big{font-size:30px}
  .avis-grid{grid-template-columns:1fr;gap:14px}
  .avis-card{padding:18px}
  .avis-form{padding:20px}

  .product-page{grid-template-columns:1fr !important;gap:20px !important}
  .gallery-wrap{position:static}
  .gallery-thumb{width:56px;height:56px}

  .grid{grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:12px}
  .card-body{padding:12px;gap:6px}
  .card-title{font-size:13px}
  .card-price{font-size:15px}
  .card-form input[type=number]{width:44px;padding:6px;font-size:13px}
  .card-form button{padding:8px;font-size:12px}
  .card-cat{font-size:10px;padding:2px 8px}

  .blog-grid{grid-template-columns:1fr;gap:16px}
  .blog-card-body{padding:16px}

  .newsletter{padding:32px 16px}
  .newsletter h2{font-size:18px}
  .newsletter form{flex-direction:column;gap:8px}
  .newsletter input{min-width:auto;width:100%}

  footer{padding:32px 16px 20px}
  .footer-grid{grid-template-columns:1fr 1fr;gap:20px}
  .footer-grid h4{font-size:14px}
  .footer-grid a{font-size:12px}

  .float-btns{bottom:14px;right:14px;gap:8px}
  .wa-cta{padding:8px 14px;font-size:12px}
  .wa-btn,.cart-float{width:48px;height:48px}
  .wa-btn svg{width:26px;height:26px}
  .cart-float svg{width:22px;height:22px}

  .cart-drawer{width:100%;max-width:100vw}

  .admin-wrap{flex-direction:column}
  .admin-side{width:100%;padding:12px 0;display:flex;overflow-x:auto;
    flex-wrap:nowrap;gap:0;white-space:nowrap}
  .admin-side h2{display:none}
  .admin-side a{padding:10px 14px;font-size:13px;border-left:0;
    border-bottom:3px solid transparent;display:inline-block}
  .admin-side a.active{border-left:0;border-bottom-color:var(--jaune)}
  .admin-side .sep{display:none}
  .admin-main{padding:16px}
  .admin-main h1{font-size:20px;margin-bottom:16px}
  .stat-grid{grid-template-columns:1fr 1fr;gap:10px;margin-bottom:20px}
  .stat-card{padding:14px}
  .stat-card .value{font-size:22px}
  .stat-card .label{font-size:12px}

  .form button{padding:12px 20px;width:100%}
  .checkout-btn{padding:14px 20px;font-size:15px}

  table{font-size:13px}
  th,td{padding:8px;font-size:12px}

  .photo-grid{grid-template-columns:repeat(auto-fill,minmax(80px,1fr));gap:8px}
}

/* ============================================================
   TRÈS PETIT MOBILE
   ============================================================ */
@media(max-width:480px){
  .features{grid-template-columns:1fr}
  .grid{grid-template-columns:1fr 1fr;gap:10px}
  .card-form{flex-direction:column}
  .card-form input[type=number]{width:100%}
  .card-form button{padding:9px}
  .footer-grid{grid-template-columns:1fr;text-align:center}
  .footer-grid ul{align-items:center}
  .hero h1{font-size:24px}
  .hero p{font-size:13px}
  .hero .btn{padding:10px 18px;font-size:13px}
  .avis-stats{flex-direction:column;gap:12px;text-align:center}
  .stat-grid{grid-template-columns:1fr}
  .header-right{gap:8px}
  .header-right .cart-btn{padding:8px 10px;font-size:12px}
  .float-btns{gap:6px}
  .wa-cta{display:none}
  .wa-btn,.cart-float{width:46px;height:46px}
  .gallery-thumbs{justify-content:flex-start;overflow-x:auto;flex-wrap:nowrap;padding-bottom:4px}
}

@supports(-webkit-touch-callout:none){
  input,textarea,select{font-size:16px}
  .cart-drawer{height:-webkit-fill-available}
}
"""
# =============================================================
# TEMPLATES HTML
# =============================================================
TEMPLATES = {}

TEMPLATES["base"] = """
<!doctype html>
<html lang="{{ g.lang }}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=5">
<title>{% block title %}{{ config.SITE_NAME }}{% endblock %}</title>
<meta name="description" content="{{ config.SITE_DESCRIPTION }}">
<link rel="icon" type="image/svg+xml" href="data:image/svg+xml;base64,{{ favicon_b64 }}">
<link rel="shortcut icon" type="image/svg+xml" href="data:image/svg+xml;base64,{{ favicon_b64 }}">
<link rel="apple-touch-icon" href="data:image/svg+xml;base64,{{ favicon_b64 }}">
<style>{{ css|safe }}</style>
</head>
<body>

<div class="topbar">
  <div class="left">
    <div class="lang-selector" id="langSel">
      <button type="button" class="btn-lang" id="btnLang">
        {{ 'globe'|icon()|safe }}
        <span class="flag">{{ config.LANGUAGES[g.lang][1] }}</span>
        <span>{{ config.LANGUAGES[g.lang][0] }}</span>
        {{ 'chevron'|icon()|safe }}
      </button>
      <div class="menu" id="langMenu">
        {% for code, info in config.LANGUAGES.items() %}
          <a href="{{ url_for('set_lang', code=code) }}" class="{% if code==g.lang %}active{% endif %}">
            <span class="flag">{{ info[1] }}</span> {{ info[0] }}
          </a>
        {% endfor %}
      </div>
    </div>
  </div>
  <div class="right">
    <span class="country-block">
      <span class="flag">{{ config.SITE_FLAG }}</span>
      <span>{{ config.SITE_COUNTRY }} · {{ config.SITE_PHONE }}</span>
      <a class="wa-mini" href="{{ wa_url() }}" target="_blank" rel="noopener" title="WhatsApp">{{ 'whatsapp'|icon()|safe }}</a>
    </span>
  </div>
</div>

<div class="header">
  <a href="{{ url_for('index') }}" class="logo">Monjaroo<span>.shop</span></a>
  <form class="search" method="get" action="{{ url_for('recherche') }}">
    <input name="q" placeholder="{{ _('search_ph') }}" value="{{ request.args.get('q','') }}">
    <button type="submit">{{ 'search'|icon()|safe }} {{ _('search') }}</button>
  </form>
  <div class="header-right">
    {% if current_user.is_authenticated and current_user.id == 'admin' %}
      <a href="{{ url_for('admin_dashboard') }}" class="admin-btn">{{ 'shield'|icon('ico')|safe }} Admin</a>
      <a href="{{ url_for('admin_logout') }}" style="color:#a32115">{{ _('logout') }}</a>
    {% elif current_user.is_authenticated %}
      <a href="{{ url_for('mon_compte') }}">{{ 'user'|icon('ico')|safe }} {{ _('account') }}</a>
      <a href="{{ url_for('deconnexion') }}" style="color:#a32115">{{ _('logout') }}</a>
    {% else %}
      <a href="{{ url_for('connexion') }}">{{ 'user'|icon('ico')|safe }} {{ _('login') }}</a>
    {% endif %}
    <button type="button" class="cart-btn" onclick="openCart();return false;">
      {{ 'cart'|icon()|safe }} {{ total_panier()|eur }} ({{ taille_panier() }})
    </button>
    <button type="button" class="burger" onclick="document.querySelector('.nav').classList.toggle('open');return false;">
      {{ 'menu'|icon('ico')|safe }}
    </button>
  </div>
</div>

<nav class="nav">
  <a href="{{ url_for('index') }}" class="{% if request.endpoint=='index' %}active{% endif %}">{{ _('home') }}</a>
  <a href="{{ url_for('medicaments') }}" class="{% if request.endpoint=='medicaments' %}active{% endif %}">{{ _('meds') }}</a>
  <a href="{{ url_for('peptides') }}" class="{% if request.endpoint=='peptides' %}active{% endif %}">{{ _('peptides') }}</a>
  <a href="{{ url_for('pilules') }}" class="{% if request.endpoint=='pilules' %}active{% endif %}">{{ _('pills') }}</a>
  <div class="dropdown">
    <span>{{ _('general') }} {{ 'chevron'|icon()|safe }}</span>
    <div class="dropdown-menu">
      <a href="{{ url_for('blog') }}">{{ _('blog') }}</a>
      <a href="{{ url_for('contact') }}">{{ _('contact') }}</a>
      <a href="{{ url_for('mon_compte') }}">{{ _('account') }}</a>
      <a href="{{ url_for('page_dynamique', slug='conditions-generales') }}">{{ _('cgv') }}</a>
      <a href="{{ url_for('page_dynamique', slug='retours-remboursements') }}">{{ _('returns') }}</a>
      <a href="{{ url_for('page_dynamique', slug='politique-confidentialite') }}">{{ _('privacy') }}</a>
      <a href="{{ url_for('faq') }}">{{ _('faq') }}</a>
    </div>
  </div>
</nav>

{% with messages = get_flashed_messages(with_categories=true) %}
  {% if messages %}
    <div class="flash">
      {% for cat, msg in messages %}<div class="flash-{{cat}}">{{ msg }}</div>{% endfor %}
    </div>
  {% endif %}
{% endwith %}

{% block content %}{% endblock %}

<section class="newsletter">
  <h2>{{ _('newsletter') }}</h2>
  <p>{{ _('newsletter_sub') }}</p>
  <form method="post" action="{{ url_for('newsletter') }}">
    <input type="email" name="email" placeholder="{{ _('email_ph') }}" required>
    <button type="submit">{{ _('subscribe') }}</button>
  </form>
</section>

<footer>
  <div class="footer-grid">
    <div>
      <h4>{{ config.SITE_NAME }}</h4>
      <p>Boutique en ligne de produits de bien-être, peptides et médicaments.</p>
    </div>
    <div>
      <h4>Menu</h4>
      <ul>
        <li><a href="{{ url_for('index') }}">{{ _('home') }}</a></li>
        <li><a href="{{ url_for('medicaments') }}">{{ _('meds') }}</a></li>
        <li><a href="{{ url_for('peptides') }}">{{ _('peptides') }}</a></li>
        <li><a href="{{ url_for('pilules') }}">{{ _('pills') }}</a></li>
        <li><a href="{{ url_for('blog') }}">{{ _('blog') }}</a></li>
      </ul>
    </div>
    <div>
      <h4>Informations</h4>
      <ul>
        <li><a href="{{ url_for('page_dynamique', slug='conditions-generales') }}">{{ _('cgv') }}</a></li>
        <li><a href="{{ url_for('page_dynamique', slug='retours-remboursements') }}">{{ _('returns') }}</a></li>
        <li><a href="{{ url_for('page_dynamique', slug='politique-confidentialite') }}">{{ _('privacy') }}</a></li>
        <li><a href="{{ url_for('faq') }}">{{ _('faq') }}</a></li>
      </ul>
    </div>
    <div>
      <h4>Contact</h4>
      <ul>
        <li>{{ config.SITE_COUNTRY }}</li>
        <li><a href="mailto:{{ config.SITE_EMAIL }}">{{ 'mail'|icon()|safe }} {{ config.SITE_EMAIL }}</a></li>
        <li><a href="tel:{{ config.SITE_PHONE }}">{{ 'phone'|icon()|safe }} {{ config.SITE_PHONE }}</a></li>
        <li><a href="{{ wa_url() }}" target="_blank">{{ 'whatsapp'|icon()|safe }} WhatsApp</a></li>
      </ul>
    </div>
  </div>
  <div class="footer-copy">Copyright © 2026 {{ config.SITE_NAME }} — {{ _('all_rights') }}</div>
</footer>

<div class="float-btns">
  <a class="wa-cta" href="{{ wa_url() }}" target="_blank" rel="noopener">{{ _('contact_us') }}</a>
  <a class="wa-btn" href="{{ wa_url() }}" target="_blank" rel="noopener" title="WhatsApp">{{ 'whatsapp'|icon()|safe }}</a>
  <button type="button" class="cart-float" onclick="openCart();return false;" title="{{ _('cart') }}">
    {{ 'cart'|icon()|safe }}
    <span class="badge" id="cartBadge" {% if taille_panier()==0 %}style="display:none"{% endif %}>{{ taille_panier() }}</span>
  </button>
</div>

<div class="cart-overlay" id="cartOverlay"></div>
<aside class="cart-drawer" id="cartDrawer">
  <div class="cart-head">
    <h3>{{ _('your_cart') }}</h3>
    <button type="button" class="cart-close" onclick="closeCart();return false;">{{ 'close'|icon()|safe }}</button>
  </div>
  <div class="cart-body" id="cartBody"><div class="cart-empty">{{ _('empty_cart') }}</div></div>
  <div class="cart-foot">
    <div class="cart-total"><span>{{ _('total') }}</span><span id="cartTotal">0,00 €</span></div>
    <a class="btn-cart" href="{{ url_for('commander') }}">{{ _('checkout') }}</a>
  </div>
</aside>

<div class="cookie-banner" id="cookieBanner" style="display:none;position:fixed;left:0;right:0;bottom:0;background:#0a2e2e;color:#e8f0ef;padding:14px 18px;justify-content:space-between;align-items:center;gap:14px;z-index:2000;font-size:13px;flex-wrap:wrap">
  <div>🍪 Cookies. En continuant, vous acceptez notre <a href="{{ url_for('page_dynamique', slug='politique-confidentialite') }}" style="color:#f5d547;text-decoration:underline">politique</a>.</div>
  <div style="display:flex;gap:10px;flex-shrink:0">
    <button type="button" onclick="refuseCookies();return false;" style="background:transparent;color:#e8f0ef;border:1px solid #3a5a5a;padding:8px 18px;border-radius:6px;font-weight:700;cursor:pointer">Refuser</button>
    <button type="button" onclick="acceptCookies();return false;" style="background:#f5d547;color:#0d5e5e;border:0;padding:8px 18px;border-radius:6px;font-weight:700;cursor:pointer">Accepter</button>
  </div>
</div>

<script>
(function(){
  var sel = document.getElementById('langSel');
  var btn = document.getElementById('btnLang');
  if(sel && btn){
    btn.addEventListener('click', function(e){
      e.preventDefault();
      e.stopPropagation();
      sel.classList.toggle('open');
    });
    var menu = sel.querySelector('.menu');
    if(menu){ menu.addEventListener('click', function(e){ e.stopPropagation(); }); }
    document.addEventListener('click', function(){ sel.classList.remove('open'); });
  }
})();

function openCart(){
  var d = document.getElementById('cartDrawer');
  var o = document.getElementById('cartOverlay');
  if(d) d.classList.add('open');
  if(o) o.classList.add('open');
  loadCart();
}
function closeCart(){
  var d = document.getElementById('cartDrawer');
  var o = document.getElementById('cartOverlay');
  if(d) d.classList.remove('open');
  if(o) o.classList.remove('open');
}
(function(){
  var o = document.getElementById('cartOverlay');
  if(o) o.addEventListener('click', closeCart);
})();

function loadCart(){
  fetch('{{ url_for("api_cart") }}').then(function(r){return r.json()}).then(function(data){
    var body = document.getElementById('cartBody');
    var total = document.getElementById('cartTotal');
    var badge = document.getElementById('cartBadge');
    if(!body || !total || !badge) return;
    total.textContent = data.total;
    if(data.count === 0){
      body.innerHTML = '<div class="cart-empty">{{ _("empty_cart") }}</div>';
      badge.style.display = 'none';
    } else {
      badge.textContent = data.count;
      badge.style.display = '';
      body.innerHTML = data.items.map(function(it){
        var img = it.image ? '<img src="' + it.image + '">' :
          '<div style="width:64px;height:64px;background:#f2f2f2;border-radius:8px"></div>';
        return '<div class="cart-item">' + img +
          '<div class="cart-item-info"><h4>' + it.nom + '</h4>' +
          '<div class="prix">' + it.prix + ' × ' + it.qte + ' = ' + it.sous_total + '</div>' +
          '<div class="cart-item-qte">' +
          '<input type="number" min="1" value="' + it.qte + '" onchange="updateQte(' + it.id + ', this.value)">' +
          '<button class="cart-item-remove" onclick="removeItem(' + it.id + ')">×</button>' +
          '</div></div></div>';
      }).join('');
    }
  }).catch(function(e){ console.error('cart error', e); });
}
function updateQte(id, qte){
  fetch('{{ url_for("api_cart_update") }}', {method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({id: id, qte: qte})}).then(loadCart);
}
function removeItem(id){
  fetch('{{ url_for("api_cart_remove") }}', {method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({id: id})}).then(loadCart);
}

function getCookie(n){
  var parts = document.cookie.split('; ');
  for(var i=0;i<parts.length;i++){ if(parts[i].indexOf(n + '=') === 0) return parts[i]; }
  return null;
}
function acceptCookies(){
  document.cookie = 'cookie_consent=accepted; max-age=' + (365*24*3600) + '; path=/';
  var el = document.getElementById('cookieBanner'); if(el) el.style.display = 'none';
}
function refuseCookies(){
  document.cookie = 'cookie_consent=refused; max-age=' + (365*24*3600) + '; path=/';
  var el = document.getElementById('cookieBanner'); if(el) el.style.display = 'none';
}
(function(){
  var el = document.getElementById('cookieBanner');
  if(el && !getCookie('cookie_consent')) el.style.display = 'flex';
})();

function togglePwd(inputId, btn){
  var inp = document.getElementById(inputId);
  if(!inp) return false;
  if(inp.type === 'password'){ inp.type = 'text'; if(btn) btn.textContent = '👁'; }
  else { inp.type = 'password'; if(btn) btn.textContent = '●'; }
  return false;
}
</script>
</body>
</html>
"""

TEMPLATES["admin_base"] = """
<!doctype html>
<html lang="{{ g.lang }}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{% block title %}Admin — {{ config.SITE_NAME }}{% endblock %}</title>
<link rel="icon" type="image/svg+xml" href="data:image/svg+xml;base64,{{ favicon_b64 }}">
<style>{{ css|safe }}</style>
</head>
<body>
<div class="admin-wrap">
  <aside class="admin-side">
    <h2>MONJAROO ADMIN</h2>
    <a href="{{ url_for('admin_dashboard') }}" class="{% if request.endpoint=='admin_dashboard' %}active{% endif %}">📊 Dashboard</a>
    <a href="{{ url_for('admin_commandes') }}" class="{% if request.endpoint=='admin_commandes' %}active{% endif %}">📦 Commandes</a>
    <a href="{{ url_for('admin_produits') }}" class="{% if request.endpoint in ['admin_produits','admin_produit_form'] %}active{% endif %}">🛒 Produits</a>
    <a href="{{ url_for('admin_categories') }}" class="{% if request.endpoint=='admin_categories' %}active{% endif %}">🗂 Catégories</a>
    <a href="{{ url_for('admin_utilisateurs') }}" class="{% if request.endpoint=='admin_utilisateurs' %}active{% endif %}">👥 Utilisateurs</a>
    <a href="{{ url_for('admin_avis') }}" class="{% if request.endpoint=='admin_avis' %}active{% endif %}">⭐ Avis</a>
    <a href="{{ url_for('admin_messages') }}" class="{% if request.endpoint=='admin_messages' %}active{% endif %}">📨 Messages</a>
    <a href="{{ url_for('admin_slides') }}" class="{% if request.endpoint=='admin_slides' %}active{% endif %}">🖼 Carrousel</a>
    <a href="{{ url_for('admin_articles') }}" class="{% if request.endpoint in ['admin_articles','admin_article_form'] %}active{% endif %}">📝 Blog</a>
    <a href="{{ url_for('admin_contenu') }}" class="{% if request.endpoint=='admin_contenu' %}active{% endif %}">🎨 Accueil</a>
    <a href="{{ url_for('admin_pages') }}" class="{% if request.endpoint in ['admin_pages','admin_page_form'] %}active{% endif %}">📄 Pages</a>
    <a href="{{ url_for('admin_faq') }}" class="{% if request.endpoint=='admin_faq' %}active{% endif %}">❓ FAQ</a>
    <div class="sep"></div>
    <a href="{{ url_for('index') }}" target="_blank">🌐 Voir le site</a>
    <a href="{{ url_for('admin_logout') }}" style="color:#ffb3b3">🚪 Déconnexion</a>
  </aside>
  <main class="admin-main">
    {% with messages = get_flashed_messages(with_categories=true) %}
      {% if messages %}
        {% for cat, msg in messages %}
          <div class="flash-{{cat}}" style="margin-bottom:12px">{{ msg }}</div>
        {% endfor %}
      {% endif %}
    {% endwith %}
    {% block content %}{% endblock %}
  </main>
</div>
</body>
</html>
"""

TEMPLATES["admin_login"] = """
{% extends "base" %}
{% block content %}
<section class="section">
  <h1 style="color:#111">Admin — Connexion</h1>
  <form method="post" action="{{ url_for('admin_login') }}" class="form" style="max-width:420px" autocomplete="off">
    <label>Identifiant (nom d'utilisateur ou email)
      <input name="identifiant" required autocomplete="off" placeholder="admin ou admin@monjaroo.shop">
    </label>
    <label>Mot de passe</label>
    <div class="pwd-wrap">
      <input type="password" name="password" id="pwd_admin" required autocomplete="new-password">
      <button type="button" class="pwd-toggle" onclick="togglePwd('pwd_admin', this); return false;">{{ 'eye'|icon()|safe }}</button>
    </div>
    <button type="submit" style="margin-top:14px">Se connecter</button>
  </form>
</section>
{% endblock %}
"""

TEMPLATES["admin_dashboard"] = """
{% extends "admin_base" %}
{% block content %}
<h1>Dashboard admin</h1>
<div class="stat-grid">
  <div class="stat-card vert"><div class="label">Produits</div><div class="value">{{ stats.produits }}</div></div>
  <div class="stat-card violet"><div class="label">Commandes</div><div class="value">{{ stats.commandes }}</div></div>
  <div class="stat-card orange"><div class="label">Avis publiés</div><div class="value">{{ stats.avis }}</div></div>
  <div class="stat-card blue"><div class="label">Utilisateurs</div><div class="value">{{ stats.users }}</div></div>
  <div class="stat-card red"><div class="label">Messages non lus</div><div class="value">{{ stats.messages }}</div></div>
  <div class="stat-card green"><div class="label">Pages légales</div><div class="value">{{ stats.pages }}</div></div>
  <div class="stat-card"><div class="label">Catégories</div><div class="value">{{ stats.categories }}</div></div>
  <div class="stat-card"><div class="label">Articles blog</div><div class="value">{{ stats.articles }}</div></div>
  <div class="stat-card"><div class="label">Slides</div><div class="value">{{ stats.slides }}</div></div>
  <div class="stat-card"><div class="label">FAQ</div><div class="value">{{ stats.faq }}</div></div>
</div>
{% endblock %}
"""

TEMPLATES["admin_commandes"] = """
{% extends "admin_base" %}
{% block content %}
<h1>Commandes</h1>
<div style="margin:14px 0">
  <a href="{{ url_for('admin_commandes') }}" style="padding:8px 14px;border-radius:6px;background:{{ '#a855f7' if not statut_filtre else '#eee' }};color:{{ '#fff' if not statut_filtre else '#111' }}">Toutes</a>
  {% for s in ['en_attente','en_cours','expediee','livree','annulee'] %}
    <a href="{{ url_for('admin_commandes', statut=s) }}" style="padding:8px 14px;border-radius:6px;margin-left:4px;background:{{ '#a855f7' if statut_filtre==s else '#eee' }};color:{{ '#fff' if statut_filtre==s else '#111' }}">{{ s }}</a>
  {% endfor %}
  <a href="{{ url_for('admin_commandes_export') }}" style="float:right;padding:8px 14px;border-radius:6px;background:var(--vert);color:#fff">Exporter CSV</a>
</div>
<table>
  <tr><th>Réf.</th><th>Date</th><th>Client</th><th>Total</th><th>Statut</th><th></th></tr>
  {% for c in commandes %}
  <tr>
    <td>{{ c.reference }}</td><td>{{ c.date|datefr }}</td>
    <td>{{ c.nom_client }}<br><small>{{ c.email }}</small></td>
    <td>{{ c.total|eur }}</td>
    <td><span class="badge-status badge-{{ c.statut }}">{{ c.statut }}</span></td>
    <td><a href="{{ url_for('admin_commande_detail', cid=c.id) }}">Détail</a></td>
  </tr>
  {% else %}<tr><td colspan="6" style="text-align:center;color:#999">Aucune commande.</td></tr>{% endfor %}
</table>
{% endblock %}
"""

TEMPLATES["admin_commande_detail"] = """
{% extends "admin_base" %}
{% block content %}
<h1>Commande {{ commande.reference }}</h1>
<p>{{ commande.date|datefr }}</p>
<h3>Client</h3>
<p><strong>{{ commande.nom_client }}</strong><br>{{ commande.email }}<br>{{ commande.telephone }}<br>{{ commande.adresse }}</p>
<h3>Articles</h3>
<table>
  <tr><th>Produit</th><th>Qté</th><th>P.U.</th><th>Sous-total</th></tr>
  {% for l in commande.lignes %}
  <tr><td>{{ l.produit_nom or (l.produit.nom if l.produit else '—') }}</td><td>{{ l.quantite }}</td><td>{{ l.prix_unitaire|eur }}</td><td>{{ (l.prix_unitaire*l.quantite)|eur }}</td></tr>
  {% endfor %}
  <tr><th colspan="3" style="text-align:right">Total</th><th>{{ commande.total|eur }}</th></tr>
</table>
<h3 style="margin-top:28px">Statut & note</h3>
<form method="post" class="form" style="max-width:520px">
  <label>Statut
    <select name="statut">
      {% for s in ['en_attente','en_cours','expediee','livree','annulee'] %}
      <option value="{{ s }}" {% if commande.statut==s %}selected{% endif %}>{{ s }}</option>
      {% endfor %}
    </select>
  </label>
  <label>Note <textarea name="note" rows="3">{{ commande.note }}</textarea></label>
  <button type="submit">Enregistrer</button>
</form>
{% endblock %}
"""

TEMPLATES["admin_utilisateurs"] = """
{% extends "admin_base" %}
{% block content %}
<h1>Utilisateurs</h1>
<table>
  <tr><th>Date</th><th>Nom</th><th>Email</th><th>Commandes</th><th></th></tr>
  {% for u in users %}
  <tr>
    <td>{{ u.date_creation|datefr }}</td><td>{{ u.nom or '—' }}</td>
    <td>{{ u.email }}</td>
    <td>{{ u.commandes|length }}</td>
    <td><form method="post" action="{{ url_for('admin_utilisateur_supprimer', uid=u.id) }}" style="display:inline"><button class="btn" onclick="return confirm('Supprimer ?')">Suppr.</button></form></td>
  </tr>
  {% else %}<tr><td colspan="5" style="text-align:center;color:#999">Aucun utilisateur.</td></tr>{% endfor %}
</table>
{% endblock %}
"""

TEMPLATES["admin_messages"] = """
{% extends "admin_base" %}
{% block content %}
<h1>Messages</h1>
<table>
  <tr><th>Date</th><th>Nom</th><th>Email</th><th>Message</th><th>Lu</th><th></th></tr>
  {% for m in messages %}
  <tr>
    <td>{{ m.date|datefr }}</td><td>{{ m.nom }}</td><td>{{ m.email }}</td>
    <td style="max-width:340px">{{ m.message }}</td>
    <td>{{ "oui" if m.lu else "non" }}</td>
    <td>
      <form method="post" action="{{ url_for('admin_message_lu', mid=m.id) }}" style="display:inline"><button class="btn">{{ "Non lu" if m.lu else "Lu" }}</button></form>
      <form method="post" action="{{ url_for('admin_message_supprimer', mid=m.id) }}" style="display:inline"><button class="btn" onclick="return confirm('Supprimer ?')">Suppr.</button></form>
    </td>
  </tr>
  {% else %}<tr><td colspan="6" style="text-align:center;color:#999">Aucun message.</td></tr>{% endfor %}
</table>
{% endblock %}
"""

TEMPLATES["admin_slides"] = """
{% extends "admin_base" %}
{% block content %}
<h1>Carrousel accueil</h1>
<form method="post" enctype="multipart/form-data" class="form" style="max-width:600px;margin-bottom:28px">
  <label>Image <input type="file" name="image_file" accept="image/*"></label>
  <label>OU URL <input name="image" placeholder="https://..."></label>
  <label>Ordre <input type="number" name="ordre" value="0"></label>
  <button type="submit">Ajouter</button>
</form>
<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:14px">
  {% for s in slides %}
  <div style="border:1px solid #ddd;border-radius:8px;padding:10px;background:#fff">
    <img src="{{ s.image }}" style="width:100%;height:130px;object-fit:cover;border-radius:6px">
    <div style="font-size:12px;color:#888;margin-top:8px">Ordre {{ s.ordre }}</div>
    <form method="post" action="{{ url_for('admin_slide_supprimer', sid=s.id) }}" style="margin-top:6px">
      <button class="btn" onclick="return confirm('Supprimer ?')">Suppr.</button>
    </form>
  </div>
  {% endfor %}
</div>
{% endblock %}
"""

TEMPLATES["admin_articles"] = """
{% extends "admin_base" %}
{% block content %}
<h1>Blog</h1>
<a class="btn-link" href="{{ url_for('admin_article_form') }}">+ Nouvel article</a>
<table>
  <tr><th>Date</th><th>Catégorie</th><th>Titre</th><th></th></tr>
  {% for a in articles %}
  <tr>
    <td>{{ a.date|datefr }}</td><td>{{ a.categorie or 'Blog' }}</td><td>{{ a.titre }}</td>
    <td>
      <a href="{{ url_for('admin_article_form', aid=a.id) }}">Éditer</a>
      <form method="post" action="{{ url_for('admin_article_supprimer', aid=a.id) }}" style="display:inline"><button class="btn" onclick="return confirm('Supprimer ?')">Suppr.</button></form>
    </td>
  </tr>
  {% endfor %}
</table>
{% endblock %}
"""

TEMPLATES["admin_article_form"] = """
{% extends "admin_base" %}
{% block content %}
<h1>{{ "Éditer" if article.id else "Nouvel" }} article</h1>
<form method="post" enctype="multipart/form-data" class="form" style="max-width:800px">
  <label>Titre <input name="titre" value="{{ article.titre or '' }}" required></label>
  <label>Catégorie <input name="categorie" value="{{ article.categorie or 'Blog' }}"></label>
  <label>Extrait <textarea name="extrait" rows="2">{{ article.extrait or '' }}</textarea></label>
  <label>Contenu <textarea name="contenu" rows="12">{{ article.contenu or '' }}</textarea></label>
  {% if article.image %}<img src="{{ article.image }}" style="max-width:300px;border-radius:8px;margin:10px 0">{% endif %}
  <label>Image <input type="file" name="image_file" accept="image/*"></label>
  <label>OU URL <input name="image" value="{{ article.image or '' }}"></label>
  <button type="submit">Enregistrer</button>
</form>
{% endblock %}
"""

TEMPLATES["admin_contenu"] = """
{% extends "admin_base" %}
{% block content %}
<h1>Contenu accueil</h1>
<form method="post" enctype="multipart/form-data" class="form" style="max-width:800px">
  <h3 style="color:#a855f7">Hero</h3>
  {% if c.hero_image %}<img src="{{ c.hero_image }}" style="max-width:300px;border-radius:8px;margin-bottom:10px">{% endif %}
  <label>Image <input type="file" name="hero_image_file" accept="image/*"></label>
  <label>OU URL <input name="hero_image" value="{{ c.hero_image }}"></label>
  <label>Badge <input name="hero_badge" value="{{ c.hero_badge }}"></label>
  <label>Titre <input name="hero_titre" value="{{ c.hero_titre }}"></label>
  <label>Texte <textarea name="hero_texte" rows="3">{{ c.hero_texte }}</textarea></label>
  <label>Texte bouton <input name="hero_btn_texte" value="{{ c.hero_btn_texte }}"></label>
  <label>Lien bouton <input name="hero_btn_lien" value="{{ c.hero_btn_lien }}"></label>
  <h3 style="color:#a855f7;margin-top:22px">Features</h3>
  <label>Feature 1 <input name="feat1" value="{{ c.feat1 }}"></label>
  <label>Feature 2 <input name="feat2" value="{{ c.feat2 }}"></label>
  <label>Feature 3 <input name="feat3" value="{{ c.feat3 }}"></label>
  <label>Feature 4 <input name="feat4" value="{{ c.feat4 }}"></label>
  <h3 style="color:#a855f7;margin-top:22px">À propos</h3>
  {% if c.about_image %}<img src="{{ c.about_image }}" style="max-width:300px;border-radius:8px;margin-bottom:10px">{% endif %}
  <label>Image <input type="file" name="about_image_file" accept="image/*"></label>
  <label>OU URL <input name="about_image" value="{{ c.about_image }}"></label>
  <label>Titre <input name="about_titre" value="{{ c.about_titre }}"></label>
  <label>Texte <textarea name="about_texte" rows="3">{{ c.about_texte }}</textarea></label>
  <h3 style="color:#a855f7;margin-top:22px">Section violette</h3>
  <label>Titre <input name="violet_titre" value="{{ c.violet_titre }}"></label>
  <label>Para 1 <textarea name="violet_p1a" rows="2">{{ c.violet_p1a }}</textarea></label>
  <label>Para 2 <textarea name="violet_p1b" rows="3">{{ c.violet_p1b }}</textarea></label>
  <label>Para 3 <textarea name="violet_p2a" rows="3">{{ c.violet_p2a }}</textarea></label>
  <label>Para 4 <textarea name="violet_p2b" rows="2">{{ c.violet_p2b }}</textarea></label>
  <button type="submit" style="margin-top:22px">Enregistrer</button>
</form>
{% endblock %}
"""

TEMPLATES["admin_produits"] = """
{% extends "admin_base" %}
{% block content %}
<h1>Produits & stock</h1>
<a class="btn-link" href="{{ url_for('admin_produit_form') }}">+ Nouveau produit</a>
<table>
<tr><th>Image</th><th>Nom</th><th>Catégorie</th><th>Prix</th><th>Stock</th><th>Photos</th><th>Actif</th><th></th></tr>
{% for p in produits %}
<tr>
  <td>{% if p.image %}<img src="{{ p.image }}" style="width:44px;height:44px;object-fit:cover;border-radius:6px">{% endif %}</td>
  <td>{{ p.nom }}<br><small>{{ p.sous_titre }}</small></td>
  <td>{{ p.categorie.nom if p.categorie else '—' }}</td>
  <td>{{ p.affichage_prix }}</td>
  <td>{{ p.stock }}</td>
  <td><span style="background:#f3e8ff;color:#a855f7;padding:2px 8px;border-radius:10px;font-size:12px;font-weight:600">{{ p.photos|length }}/5</span></td>
  <td>{{ "oui" if p.actif else "non" }}</td>
  <td>
    <a href="{{ url_for('admin_produit_form', pid=p.id) }}">Éditer</a>
    <form method="post" action="{{ url_for('admin_produit_supprimer', pid=p.id) }}" style="display:inline"><button class="btn" onclick="return confirm('Supprimer ?')">Suppr.</button></form>
  </td>
</tr>
{% endfor %}
</table>
{% endblock %}
"""

TEMPLATES["admin_produit_form"] = """
{% extends "admin_base" %}
{% block content %}
<h1>{{ "Éditer" if produit.id else "Nouveau" }} produit</h1>
<form method="post" enctype="multipart/form-data" class="form" style="max-width:700px">
  <label>Nom <input name="nom" value="{{ produit.nom or '' }}" required></label>
  <label>Sous-titre <input name="sous_titre" value="{{ produit.sous_titre or '' }}"></label>
  <label>Description <textarea name="description" rows="4">{{ produit.description or '' }}</textarea></label>
  <label>Prix min (€) <input type="number" step="0.01" name="prix" value="{{ produit.prix or 0 }}" required></label>
  <label>Prix max (€) — 0 si unique <input type="number" step="0.01" name="prix_max" value="{{ produit.prix_max or 0 }}"></label>
  <label>Stock <input type="number" name="stock" value="{{ produit.stock or 0 }}"></label>
  {% if produit.image %}<img src="{{ produit.image }}" style="max-width:200px;border-radius:8px;margin:10px 0">{% endif %}
  <label>Image principale (upload) <input type="file" name="image_file" accept="image/*"></label>
  <label>OU URL <input name="image" value="{{ produit.image or '' }}"></label>
  <label>Catégorie
    <select name="categorie_id">
      <option value="">—</option>
      {% for c in categories %}<option value="{{ c.id }}" {% if produit.categorie_id==c.id %}selected{% endif %}>{{ c.nom }}</option>{% endfor %}
    </select>
  </label>
  <label><input type="checkbox" name="actif" {% if produit.actif %}checked{% endif %}> Actif</label>
  <button type="submit">Enregistrer</button>
</form>
{% endblock %}
"""

TEMPLATES["admin_categories"] = """
{% extends "admin_base" %}
{% block content %}
<h1>Catégories</h1>
<form method="post" class="form" style="max-width:500px;margin-bottom:28px">
  <label>Nom <input name="nom" required></label>
  <label>Ordre <input type="number" name="ordre" value="0"></label>
  <button type="submit">Ajouter</button>
</form>
<table>
  <tr><th>Ordre</th><th>Nom</th><th>Slug</th><th></th></tr>
  {% for c in categories %}
  <tr>
    <td>{{ c.ordre }}</td><td>{{ c.nom }}</td><td>{{ c.slug }}</td>
    <td><form method="post" action="{{ url_for('admin_categorie_supprimer', cid=c.id) }}" style="display:inline"><button class="btn" onclick="return confirm('Supprimer ?')">Suppr.</button></form></td>
  </tr>
  {% endfor %}
</table>
{% endblock %}
"""

TEMPLATES["admin_pages"] = """
{% extends "admin_base" %}
{% block content %}
<h1>Pages légales</h1>
<a class="btn-link" href="{{ url_for('admin_page_form') }}">+ Nouvelle page</a>
<table>
<tr><th>Titre</th><th>Slug</th><th>Menu</th><th></th></tr>
{% for pg in pages %}
<tr>
  <td>{{ pg.titre }}</td><td>{{ pg.slug }}</td>
  <td>{{ "oui" if pg.afficher_menu else "non" }}</td>
  <td>
    <a href="{{ url_for('admin_page_form', pid=pg.id) }}">Éditer</a>
    <form method="post" action="{{ url_for('admin_page_supprimer', pid=pg.id) }}" style="display:inline"><button class="btn" onclick="return confirm('Supprimer ?')">Suppr.</button></form>
  </td>
</tr>
{% endfor %}
</table>
{% endblock %}
"""

TEMPLATES["admin_page_form"] = """
{% extends "admin_base" %}
{% block content %}
<h1>{{ "Éditer" if page.id else "Nouvelle" }} page</h1>
<form method="post" class="form" style="max-width:900px">
  <label>Titre <input name="titre" value="{{ page.titre or '' }}" required></label>
  <label>Slug <input name="slug" value="{{ page.slug or '' }}"></label>
  <label>Contenu (HTML) <textarea name="contenu" rows="20">{{ page.contenu or '' }}</textarea></label>
  <label>Ordre <input type="number" name="ordre" value="{{ page.ordre or 0 }}"></label>
  <label><input type="checkbox" name="afficher_menu" {% if page.afficher_menu %}checked{% endif %}> Afficher dans le menu</label>
  <button type="submit">Enregistrer</button>
</form>
{% endblock %}
"""

TEMPLATES["admin_avis"] = """
{% extends "admin_base" %}
{% block content %}
<h1>Avis clients</h1>
<form method="post" class="form" style="max-width:600px;margin-bottom:28px">
  <label>Nom <input name="nom" required></label>
  <label>Rôle <input name="role" value="Client"></label>
  <label>Note <input type="number" name="note" value="5" min="1" max="5"></label>
  <label>Texte <textarea name="texte" rows="4" required></textarea></label>
  <label><input type="checkbox" name="valide" checked> Publier</label>
  <button type="submit">Ajouter</button>
</form>
<table>
  <tr><th>Date</th><th>Nom</th><th>Note</th><th>Texte</th><th>Statut</th><th></th></tr>
  {% for a in avis %}
  <tr>
    <td>{{ a.date|datefr }}</td><td>{{ a.nom }}</td>
    <td>{{ a.note }}</td>
    <td style="max-width:340px">{{ a.texte[:120] }}{% if a.texte|length > 120 %}…{% endif %}</td>
    <td>{{ "Publié" if a.valide else "Attente" }}</td>
    <td>
      <form method="post" action="{{ url_for('admin_avis_toggle', aid=a.id) }}" style="display:inline"><button class="btn">{{ "Dépublier" if a.valide else "Publier" }}</button></form>
      <form method="post" action="{{ url_for('admin_avis_supprimer', aid=a.id) }}" style="display:inline"><button class="btn" onclick="return confirm('Supprimer ?')">Suppr.</button></form>
    </td>
  </tr>
  {% endfor %}
</table>
{% endblock %}
"""

TEMPLATES["admin_faq"] = """
{% extends "admin_base" %}
{% block content %}
<h1>FAQ</h1>
<form method="post" class="form" style="max-width:600px;margin-bottom:28px">
  <label>Question <input name="question" required></label>
  <label>Réponse <textarea name="reponse" rows="4" required></textarea></label>
  <button type="submit">Ajouter</button>
</form>
{% for q in questions %}
<div style="background:#fff;border:1px solid #ddd;padding:14px;border-radius:6px;margin-bottom:10px">
  <strong>{{ q.question }}</strong>
  <form method="post" action="{{ url_for('admin_faq_supprimer', fid=q.id) }}" style="display:inline;float:right"><button class="btn">Suppr.</button></form>
  <p style="color:#555">{{ q.reponse }}</p>
</div>
{% endfor %}
{% endblock %}
"""

TEMPLATES["admin_produit_photos"] = """
{% extends "admin_base" %}
{% block content %}
<h1>Photos du produit : {{ produit.nom }}</h1>
<p style="color:#666;margin-bottom:20px">
  <a href="{{ url_for('admin_produit_form', pid=produit.id) }}">← Retour à l'édition du produit</a>
</p>

<div class="photo-upload-section">
  <h3>
    {{ 'camera'|icon()|safe }} {{ _('photos_upload') }}
    <span class="photo-counter">{{ produit.photos|length }} / {{ MAX_PHOTOS }}</span>
  </h3>
  <p class="hint">{{ _('photos_max') }}</p>

  {% if produit.photos|length >= MAX_PHOTOS %}
    <div style="padding:12px;background:#fef3c7;color:#92400e;border-radius:6px;font-size:13px">
      ⚠️ Maximum atteint ({{ MAX_PHOTOS }} photos). Supprimez une photo avant d'en ajouter une nouvelle.
    </div>
  {% else %}
    <form method="post" enctype="multipart/form-data"
          action="{{ url_for('admin_produit_photo_upload', pid=produit.id) }}">
      <input type="file" name="photos" accept="image/*" multiple required>
      <button type="submit">{{ 'check'|icon()|safe }} {{ _('upload') }}</button>
    </form>
  {% endif %}
</div>

{% if produit.photos %}
  <h3 style="color:var(--vert);margin-top:28px">{{ _('photos_current') }}</h3>
  <div class="photo-grid">
    {% for photo in produit.photos %}
    <div class="photo-item">
      <img src="{{ photo.chemin }}" alt="Photo {{ loop.index }}">
      <form method="post"
            action="{{ url_for('admin_produit_photo_supprimer', pid=produit.id, photo_id=photo.id) }}"
            style="position:absolute;top:6px;right:6px;margin:0">
        <button type="submit" class="del-btn"
                onclick="return confirm('Supprimer cette photo ?')"
                title="{{ _('delete') }}">×</button>
      </form>
    </div>
    {% endfor %}
  </div>
{% else %}
  <p style="color:#999;margin-top:20px">Aucune photo pour ce produit. Ajoutez-en jusqu'à {{ MAX_PHOTOS }}.</p>
{% endif %}

{% endblock %}
"""

TEMPLATES["partial_card"] = """
<div class="card">
  <a href="{{ url_for('produit_detail', slug=p.slug) }}">
    <div class="card-img">
      {% if p.image %}<img src="{{ p.image }}" alt="{{ p.nom }}">
      {% elif p.photos %}<img src="{{ p.photos[0].chemin }}" alt="{{ p.nom }}">
      {% else %}<span style="color:#ccc">image</span>{% endif %}
    </div>
  </a>
  <div class="card-body">
    {% if p.sous_titre %}<span class="card-cat">{{ p.sous_titre }}</span>{% endif %}
    <a href="{{ url_for('produit_detail', slug=p.slug) }}"><h3 class="card-title">{{ p.nom }}</h3></a>
    <div class="card-price">{{ p.affichage_prix }}</div>
    {% if p.prix_max and p.prix_max > p.prix %}
      <a class="btn-options" href="{{ url_for('produit_detail', slug=p.slug) }}" style="text-align:center;text-decoration:none;padding:10px;border-radius:6px;font-weight:600;font-size:13px">{{ _('select_options') }}</a>
      <div class="card-note">{{ _('product_variants') }}</div>
    {% else %}
      <form class="card-form" method="post" action="{{ url_for('panier_ajouter', produit_id=p.id) }}">
        <input type="number" name="quantite" value="1" min="1">
        <button type="submit">{{ _('add_to_cart') }}</button>
      </form>
    {% endif %}
  </div>
</div>
"""

TEMPLATES["index"] = """
{% extends "base" %}
{% block content %}
<section class="hero">
  <div class="hero-bg">
    {% for s in slides %}
      <div class="hero-slide {% if loop.first %}active{% endif %}" style="background-image:url('{{ s.image }}')"></div>
    {% endfor %}
    {% if not slides %}
      <div class="hero-slide active" style="background-image:url('{{ get_contenu('hero_image','') }}')"></div>
    {% endif %}
  </div>
  <div class="hero-inner">
    <div class="hero-badge"><span class="dot">{{ 'heart'|icon()|safe }}</span>
      <span>{{ get_contenu('hero_badge', _('welcome')) }}</span></div>
    <h1>{{ get_contenu('hero_titre', _('hero_title')) }}</h1>
    <p>{{ get_contenu('hero_texte', _('hero_text')) }}</p>
    <a class="btn" href="{{ get_contenu('hero_btn_lien','/peptides') }}">{{ get_contenu('hero_btn_texte', _('buy_now')) }}</a>
  </div>
  {% if slides|length > 1 %}
  <div class="hero-dots">
    {% for s in slides %}<span class="{% if loop.first %}active{% endif %}" onclick="gotoSlide({{ loop.index0 }})"></span>{% endfor %}
  </div>
  {% endif %}
</section>

<section class="features">
  <div class="feature"><div class="ico">{{ 'home'|icon()|safe }}</div><p>{{ get_contenu('feat1', _('features_home')) }}</p></div>
  <div class="feature"><div class="ico">{{ 'tag'|icon()|safe }}</div><p>{{ get_contenu('feat2', _('features_price')) }}</p></div>
  <div class="feature"><div class="ico">{{ 'truck'|icon()|safe }}</div><p>{{ get_contenu('feat3', _('features_ship')) }}</p></div>
  <div class="feature"><div class="ico">{{ 'support'|icon()|safe }}</div><p>{{ get_contenu('feat4', _('features_support')) }}</p></div>
</section>

<section class="section">
  <div class="about">
    <div><img src="{{ get_contenu('about_image','') }}" alt="À propos"></div>
    <div>
      <div class="label">{{ _('about_us') }}</div>
      <h2>{{ get_contenu('about_titre', _('about_title')) }}</h2>
      <p>{{ get_contenu('about_texte', _('about_text')) }}</p>
    </div>
  </div>
</section>

<section class="violet-section">
  <div class="violet-inner">
    <h2>{{ get_contenu('violet_titre', _('discover')) }}</h2>
    <h3>{{ _('peptides') }}</h3>
    <p>{{ get_contenu('violet_p1a',"L'innovation commence par de bonnes bases.") }}</p>
    <p>{{ get_contenu('violet_p1b','Nos peptides sont conçus pour la recherche de pointe.') }}</p>
    <h3>{{ _('meds') }}</h3>
    <p>{{ get_contenu('violet_p2a','Vous achetez des médicaments en ligne ?') }}</p>
    <p>{{ get_contenu('violet_p2b','Commandez facilement et en toute fiabilité.') }}</p>
  </div>
</section>

<section class="section">
  <div class="avis-label">{{ _('reviews') }}</div>
  <h2 class="avis-title">{{ _('reviews_title') }}</h2>
  <div class="avis-stats">
    <div><div class="big">{{ note_moyenne }}</div><div style="color:#666;font-size:13px">/ 5</div></div>
    <div>
      <div class="stars">{% for i in range(1,6) %}{{ ('star' if i <= note_moyenne|round else 'star-o')|icon()|safe }}{% endfor %}</div>
      <div style="color:#666;font-size:13px;margin-top:4px"><strong>{{ nb_avis }}</strong> avis</div>
    </div>
  </div>
  <div class="avis-grid">
    {% for a in avis %}
    <div class="avis-card">
      <span class="quote">"</span>
      <div class="avis-stars">{% for i in range(1,6) %}{{ ('star' if i <= a.note else 'star-o')|icon()|safe }}{% endfor %}</div>
      <div class="avis-nom">{{ a.nom }}</div>
      <div class="avis-role">{{ a.role }}</div>
      <div class="avis-texte">{{ a.texte }}</div>
      <div class="avis-footer">{{ a.date|datefr }}</div>
    </div>
    {% endfor %}
  </div>
  <div class="avis-form">
    <h3>{{ _('leave_review') }}</h3>
    <p class="sub">{{ _('message') }}</p>
    <form method="post" action="{{ url_for('poster_avis') }}" class="form">
      <label>{{ _('full_name') }} <input name="nom" required maxlength="80"></label>
      <label>{{ _('email') }} <input name="role" placeholder="Client" maxlength="60"></label>
      <label>Note</label>
      <div class="stars-input">
        {% for i in [5,4,3,2,1] %}
          <input type="radio" id="star{{i}}" name="note" value="{{i}}" {% if i==5 %}checked{% endif %} hidden>
          <label for="star{{i}}">{{ 'star'|icon()|safe }}</label>
        {% endfor %}
      </div>
      <label>{{ _('message') }} <textarea name="texte" rows="4" required maxlength="600"></textarea></label>
      <button type="submit">{{ _('post_review') }}</button>
    </form>
  </div>
</section>

<script>
(function(){
  var slides = document.querySelectorAll('.hero-slide');
  var dots = document.querySelectorAll('.hero-dots span');
  if(slides.length < 2) return;
  var current = 0;
  function show(i){
    slides.forEach(function(s,k){ s.classList.toggle('active', k===i); });
    dots.forEach(function(d,k){ d.classList.toggle('active', k===i); });
    current = i;
  }
  window.gotoSlide = show;
  setInterval(function(){ show((current+1)%slides.length); }, 5000);
})();
</script>
{% endblock %}
"""

TEMPLATES["categorie_liste"] = """
{% extends "base" %}
{% block content %}
<section class="section-sm">
  <div style="font-size:13px;color:#888">
    <a href="{{ url_for('index') }}">{{ _('home') }}</a> / <span>{{ titre }}</span>
  </div>
</section>
<section class="section" style="padding-top:0">
  <h1 style="color:#111">{{ titre }}</h1>
  {% if sous_titre %}<p style="color:#555;margin-bottom:28px">{{ sous_titre }}</p>{% endif %}
  <div class="grid">
    {% for p in produits %}{% include "partial_card" %}{% else %}<p>Aucun produit.</p>{% endfor %}
  </div>
</section>
{% endblock %}
"""

TEMPLATES["recherche"] = """
{% extends "base" %}
{% block content %}
<section class="section">
  <h1 style="color:#111">{{ _('search') }} "{{ q }}"</h1>
  {% if produits %}
  <div class="grid">{% for p in produits %}{% include "partial_card" %}{% endfor %}</div>
  {% else %}<p>Aucun résultat.</p>{% endif %}
</section>
{% endblock %}
"""

TEMPLATES["produit"] = """
{% extends "base" %}
{% block content %}
<section class="section">
  <div class="product-page">
    <div>
      <div class="gallery-wrap">
        {% set photos = produit.toutes_photos %}
        {% if photos %}
          <div class="gallery-main" id="galleryMain">
            <span class="counter" id="galleryCounter">1 / {{ photos|length }}</span>

            {% for photo in photos %}
              <div class="slide {% if loop.first %}active{% endif %}"
                   style="background-image:url('{{ photo }}')"
                   data-index="{{ loop.index0 }}"></div>
            {% endfor %}

            {% if photos|length > 1 %}
              <button type="button" class="nav-btn prev" onclick="galleryPrev();return false;">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="m15 18-6-6 6-6"/></svg>
              </button>
              <button type="button" class="nav-btn next" onclick="galleryNext();return false;">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="m9 18 6-6-6-6"/></svg>
              </button>

              <div class="dots" id="galleryDots">
                {% for photo in photos %}
                  <span class="{% if loop.first %}active{% endif %}"
                        onclick="galleryShow({{ loop.index0 }});return false;"></span>
                {% endfor %}
              </div>
            {% endif %}
          </div>

          {% if photos|length > 1 %}
            <div class="gallery-thumbs" id="galleryThumbs">
              {% for photo in photos %}
                <div class="gallery-thumb {% if loop.first %}active{% endif %}"
                     style="background-image:url('{{ photo }}')"
                     onclick="galleryShow({{ loop.index0 }});return false;"></div>
              {% endfor %}
            </div>
          {% endif %}
        {% else %}
          <div class="gallery-main">
            <div class="slide active" style="background:#f5f5f5;display:flex;align-items:center;justify-content:center;color:#ccc">
              Aucune photo disponible
            </div>
          </div>
        {% endif %}
      </div>
    </div>

    <div>
      {% if produit.sous_titre %}<span class="card-cat">{{ produit.sous_titre }}</span>{% endif %}
      <h1 style="color:#111">{{ produit.nom }}</h1>
      <div class="card-price" style="font-size:24px">{{ produit.affichage_prix }}</div>
      <div style="margin:18px 0;color:#555">{{ produit.description|safe }}</div>

      {% if produit.prix_max and produit.prix_max > produit.prix %}
        <div style="padding:18px;background:#f7f7f9;border-radius:10px;margin-bottom:18px">
          <strong style="color:var(--vert)">{{ _('select_options') }}</strong>
          <form method="post" action="{{ url_for('panier_ajouter', produit_id=produit.id) }}"
                style="display:flex;gap:10px;align-items:center;margin-top:12px;flex-wrap:wrap">
            <select name="quantite" style="padding:10px;border:1px solid var(--border);border-radius:6px;flex:1;min-width:180px">
              <option value="1">1 — {{ produit.prix|eur }}</option>
              <option value="2">2 — {{ (produit.prix*2)|eur }}</option>
              <option value="3">3 — {{ (produit.prix*3)|eur }}</option>
            </select>
            <button type="submit" class="btn-link" style="margin:0;border:0;cursor:pointer">{{ _('add_to_cart') }}</button>
          </form>
        </div>
      {% else %}
        <form method="post" action="{{ url_for('panier_ajouter', produit_id=produit.id) }}"
              style="display:flex;gap:10px;max-width:340px;flex-wrap:wrap">
          <input type="number" name="quantite" value="1" min="1"
                 style="width:80px;padding:10px;border:1px solid var(--border);border-radius:8px">
          <button type="submit" class="btn-link"
                  style="flex:1;padding:12px;margin:0;border:0;cursor:pointer;min-width:160px">{{ _('add_to_cart') }}</button>
        </form>
      {% endif %}

      <a href="{{ wa_url('Bonjour, je souhaite commander : ' ~ produit.nom) }}"
         target="_blank" rel="noopener"
         style="display:inline-flex;align-items:center;gap:8px;margin-top:14px;
                background:#25d366;color:#fff;padding:12px 20px;border-radius:8px;font-weight:600">
        {{ 'whatsapp'|icon()|safe }} {{ _('order_wa') }}
      </a>
    </div>
  </div>
</section>

<script>
(function(){
  var slides = document.querySelectorAll('.gallery-main .slide');
  var dots = document.querySelectorAll('#galleryDots span');
  var thumbs = document.querySelectorAll('#galleryThumbs .gallery-thumb');
  var counter = document.getElementById('galleryCounter');
  if(slides.length < 2) return;
  var current = 0;
  var autoTimer = null;

  function show(i){
    if(i < 0) i = slides.length - 1;
    if(i >= slides.length) i = 0;
    slides.forEach(function(s,k){ s.classList.toggle('active', k===i); });
    dots.forEach(function(d,k){ d.classList.toggle('active', k===i); });
    thumbs.forEach(function(t,k){ t.classList.toggle('active', k===i); });
    if(counter) counter.textContent = (i+1) + ' / ' + slides.length;
    current = i;
  }

  window.galleryShow = function(i){ show(i); restartAuto(); };
  window.galleryNext = function(){ show(current + 1); restartAuto(); };
  window.galleryPrev = function(){ show(current - 1); restartAuto(); };

  function restartAuto(){
    if(autoTimer) clearInterval(autoTimer);
    autoTimer = setInterval(function(){ show(current + 1); }, 4000);
  }

  /* Défilement automatique toutes les 4 secondes */
  restartAuto();

  /* Pause au survol */
  var main = document.getElementById('galleryMain');
  if(main){
    main.addEventListener('mouseenter', function(){ if(autoTimer) clearInterval(autoTimer); });
    main.addEventListener('mouseleave', restartAuto);
  }
})();
</script>
{% endblock %}
"""

TEMPLATES["blog"] = """
{% extends "base" %}
{% block content %}
<section class="section">
  <div class="section-sm" style="padding:0">
    <div style="font-size:13px;color:#888"><a href="{{ url_for('index') }}">{{ _('home') }}</a> / <span>{{ _('blog') }}</span></div>
  </div>
  <h1 style="color:#111;margin-top:8px">{{ _('blog') }}</h1>
  <p style="color:#666;margin-bottom:32px">{{ _('blog_intro') }}</p>
  <div class="blog-grid">
    {% for a in articles %}
    <article class="blog-card">
      {% if a.image %}<img src="{{ a.image }}" alt="{{ a.titre }}">{% endif %}
      <div class="blog-card-body">
        <div class="cat-label">{{ a.categorie or 'Blog' }}</div>
        <div class="date">{{ a.date|datefr }}</div>
        <h3>{{ a.titre }}</h3>
        <p>{{ a.extrait }}</p>
        <a class="read" href="{{ url_for('blog_article', slug=a.slug) }}">{{ _('read_more') }} →</a>
      </div>
    </article>
    {% else %}<p>Aucun article.</p>{% endfor %}
  </div>
</section>
{% endblock %}
"""

TEMPLATES["blog_article"] = """
{% extends "base" %}
{% block content %}
<section class="section">
  <div style="font-size:13px;color:#888;margin-bottom:8px">
    <a href="{{ url_for('blog') }}">{{ _('blog') }}</a> / <span>{{ article.titre }}</span>
  </div>
  <div class="cat-label" style="color:var(--violet);font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:.5px;margin-bottom:6px">{{ article.categorie or 'Blog' }}</div>
  <h1 style="color:#111">{{ article.titre }}</h1>
  <div style="color:#999;font-size:13px;font-weight:600;margin-bottom:22px">{{ article.date|datefr }}</div>
  {% if article.image %}<img src="{{ article.image }}" alt="{{ article.titre }}" style="width:100%;max-width:800px;border-radius:12px;margin-bottom:22px">{% endif %}
  <div style="max-width:800px;color:#333;font-size:15px;line-height:1.85">{{ article.contenu|safe }}</div>
  <p style="margin-top:32px"><a href="{{ url_for('blog') }}" style="color:var(--violet);font-weight:600">← {{ _('blog') }}</a></p>
</section>
{% endblock %}
"""

TEMPLATES["connexion"] = """
{% extends "base" %}
{% block content %}
<section class="section">
  <h1 style="color:#111">{{ _('login') }}</h1>
  <form method="post" class="form" style="max-width:420px">
    <label>{{ _('email') }} <input name="email" required autocomplete="email"></label>
    <label>{{ _('password') }}</label>
    <div class="pwd-wrap">
      <input type="password" name="password" id="pwd_login" required autocomplete="current-password">
      <button type="button" class="pwd-toggle" onclick="togglePwd('pwd_login', this);return false;">{{ 'eye'|icon()|safe }}</button>
    </div>
    <button type="submit" style="margin-top:14px">{{ _('login') }}</button>
  </form>
  <p style="margin-top:20px">{{ _('register') }} ? <a href="{{ url_for('inscription') }}" style="color:var(--violet);font-weight:600">{{ _('register') }}</a></p>
</section>
{% endblock %}
"""

TEMPLATES["inscription"] = """
{% extends "base" %}
{% block content %}
<section class="section">
  <h1 style="color:#111">{{ _('register') }}</h1>
  <form method="post" class="form" style="max-width:420px">
    <label>{{ _('full_name') }} <input name="nom" required></label>
    <label>{{ _('email') }} <input type="email" name="email" required autocomplete="email"></label>
    <label>{{ _('password') }}</label>
    <div class="pwd-wrap">
      <input type="password" name="password" id="pwd_insc" required minlength="6" autocomplete="new-password">
      <button type="button" class="pwd-toggle" onclick="togglePwd('pwd_insc', this);return false;">{{ 'eye'|icon()|safe }}</button>
    </div>
    <label>{{ _('confirm_password') }}</label>
    <div class="pwd-wrap">
      <input type="password" name="password2" id="pwd_insc2" required minlength="6" autocomplete="new-password">
      <button type="button" class="pwd-toggle" onclick="togglePwd('pwd_insc2', this);return false;">{{ 'eye'|icon()|safe }}</button>
    </div>
    <button type="submit" style="margin-top:14px">{{ _('register') }}</button>
  </form>
  <p style="margin-top:20px">{{ _('login') }} ? <a href="{{ url_for('connexion') }}" style="color:var(--violet);font-weight:600">{{ _('login') }}</a></p>
</section>
{% endblock %}
"""

TEMPLATES["mon_compte"] = """
{% extends "base" %}
{% block content %}
<section class="section">
  <h1 style="color:#111">{{ _('account') }}</h1>
  {% if current_user.is_authenticated and current_user.id != 'admin' %}
    <p>{{ _('welcome_back') }} <strong>{{ current_user.nom or current_user.email }}</strong></p>
    <h3 style="margin-top:22px">{{ _('my_orders') }}</h3>
    {% if current_user.commandes %}
      <table>
        <tr><th>Réf.</th><th>Date</th><th>Total</th><th>Statut</th></tr>
        {% for c in current_user.commandes %}
        <tr>
          <td>{{ c.reference }}</td><td>{{ c.date|datefr }}</td>
          <td>{{ c.total|eur }}</td>
          <td><span class="badge-status badge-{{ c.statut }}">{{ c.statut }}</span></td>
        </tr>
        {% endfor %}
      </table>
    {% else %}<p style="color:#777">{{ _('no_orders') }}</p>{% endif %}
    <p style="margin-top:22px"><a href="{{ url_for('deconnexion') }}" style="color:#a32115;font-weight:600">{{ _('logout') }}</a></p>
  {% elif current_user.is_authenticated and current_user.id == 'admin' %}
    <p>Admin connecté</p>
    <p><a class="btn-link" href="{{ url_for('admin_dashboard') }}">Dashboard admin</a></p>
  {% else %}
    <a class="btn-link" href="{{ url_for('connexion') }}">{{ _('login') }}</a>
    <a class="btn-link" href="{{ url_for('inscription') }}" style="background:var(--vert)">{{ _('register') }}</a>
  {% endif %}
</section>
{% endblock %}
"""

TEMPLATES["faq"] = """
{% extends "base" %}
{% block content %}
<section class="section">
  <div style="font-size:13px;color:#888"><a href="{{ url_for('index') }}">{{ _('home') }}</a> / <span>FAQ</span></div>
  <h1 style="color:#111;margin-top:8px">{{ _('faq') }}</h1>
  <h3 style="color:var(--vert);margin:0 0 6px;font-size:20px">{{ _('faq_intro') }}</h3>
  <p style="color:#666;margin-bottom:28px">{{ _('faq_sub') }}</p>

  {% for q in questions %}
    <details><summary>{{ q.question }}</summary><p>{{ q.reponse|safe }}</p></details>
  {% else %}
    <p>Aucune question.</p>
  {% endfor %}
</section>
{% endblock %}
"""

TEMPLATES["page_dynamique"] = """
{% extends "base" %}
{% block content %}
<section class="section legal">
  <div style="font-size:13px;color:#888;margin-bottom:8px">
    <a href="{{ url_for('index') }}">{{ _('home') }}</a> / <span>{{ page.titre }}</span>
  </div>
  <h1 style="color:#111">{{ page.titre }}</h1>
  <div style="color:#333;font-size:15px;line-height:1.8;max-width:900px;margin-top:22px">{{ page.contenu|safe }}</div>
</section>
{% endblock %}
"""

TEMPLATES["contact"] = """
{% extends "base" %}
{% block content %}
<section class="section">
  <h1 style="color:#111">{{ _('contact') }}</h1>
  <p style="color:#666;margin-bottom:18px">{{ _('contact_desc') }}</p>
  <form method="post" class="form" style="max-width:520px">
    <label>{{ _('full_name') }} <input name="nom" required></label>
    <label>{{ _('email') }} <input type="email" name="email" required></label>
    <label>{{ _('message') }} <textarea name="message" rows="5" required></textarea></label>
    <button type="submit">{{ _('send') }}</button>
  </form>
</section>
{% endblock %}
"""

TEMPLATES["commander"] = """
{% extends "base" %}
{% block content %}
<section class="section">
  <h1 style="color:#111">{{ _('checkout') }}</h1>

  {% if items %}
  <div style="background:#fff;border:1px solid var(--border);border-radius:12px;padding:18px;margin-bottom:22px">
    <h3 style="margin:0 0 14px;color:#111">{{ _('order_summary') }}</h3>
    <table>
      <tr><th>Produit</th><th>Qté</th><th>Prix</th><th>Sous-total</th></tr>
      {% for it in items %}
      <tr>
        <td>{{ it.produit.nom }}</td>
        <td>{{ it.quantite }}</td>
        <td>{{ it.produit.prix|eur }}</td>
        <td>{{ it.sous_total|eur }}</td>
      </tr>
      {% endfor %}
      <tr><th colspan="3" style="text-align:right">{{ _('total') }}</th><th>{{ total|eur }}</th></tr>
    </table>
  </div>

  <div style="background:#e8f0ff;padding:14px;border-radius:8px;margin-bottom:20px;font-size:14px;color:#1e3a8a">
    ℹ️ {{ _('guest_note') }}
  </div>

  <h2 style="font-size:20px;color:#111;margin-bottom:8px">{{ _('order_info_title') }}</h2>
  <p style="color:#666;font-size:14px;margin-bottom:18px">{{ _('order_info_sub') }}</p>

  <form method="post" action="{{ url_for('commander') }}" class="form" style="max-width:520px">
    <label>{{ _('full_name') }} <input name="nom" value="{{ current_user.nom if current_user.is_authenticated and current_user.id != 'admin' else '' }}" required></label>
    <label>{{ _('email') }} <input type="email" name="email" value="{{ current_user.email if current_user.is_authenticated and current_user.id != 'admin' else '' }}" required></label>
    <label>{{ _('phone') }} <input name="telephone" required></label>
    <label>{{ _('address') }} <textarea name="adresse" rows="3" required></textarea></label>
    <button type="submit" class="checkout-btn">
      {{ 'whatsapp'|icon()|safe }} {{ _('pay_whatsapp') }}
    </button>
  </form>
  {% else %}
  <p>{{ _('empty_cart') }}</p>
  <a class="btn-link" href="{{ url_for('index') }}">{{ _('home') }}</a>
  {% endif %}
</section>
{% endblock %}
"""

TEMPLATES["confirmation"] = """
{% extends "base" %}
{% block content %}
<section class="section" style="text-align:center;padding:80px 24px">
  <div style="max-width:600px;margin:0 auto">
    <div style="width:70px;height:70px;border-radius:50%;background:#25d366;display:flex;align-items:center;justify-content:center;margin:0 auto 22px;color:#fff">
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="width:38px;height:38px"><path d="m4 12 5 5 11-11"/></svg>
    </div>
    <h1 style="color:#111;margin-bottom:14px">{{ _('thank_you') }}</h1>
    <p style="color:#555;font-size:15px;margin-bottom:6px">{{ _('order_saved') }}</p>
    <p style="color:#555;font-size:15px;margin-bottom:22px">Réf. : <strong style="color:var(--vert)">{{ commande.reference }}</strong></p>

    <div style="background:#f7f7f9;border-radius:12px;padding:22px;margin-top:20px">
      <p style="font-weight:600;color:#111;margin-bottom:10px">{{ _('last_step') }}</p>
      <p style="color:#666;font-size:14px;margin-bottom:18px">{{ _('we_respond') }}</p>
      <a href="{{ wa_url(wa_message) }}" target="_blank" rel="noopener"
         style="display:inline-flex;align-items:center;gap:10px;background:#25d366;color:#fff;padding:14px 26px;border-radius:10px;font-weight:700;font-size:15px;text-decoration:none">
        {{ 'whatsapp'|icon()|safe }} {{ _('send_whatsapp') }}
      </a>
    </div>

    <p style="margin-top:28px"><a href="{{ url_for('index') }}" style="color:var(--violet);font-weight:600">← {{ _('back_home') }}</a></p>
  </div>
</section>
{% endblock %}
"""

TEMPLATES["404"] = """
{% extends "base" %}
{% block content %}
<section class="error-page">
  <h1>404</h1>
  <p>{{ _('page_not_found') }}</p>
  <a class="btn-link" href="{{ url_for('index') }}">{{ _('back_home') }}</a>
</section>
{% endblock %}
"""

app.jinja_loader = DictLoader(TEMPLATES)


@app.context_processor
def inject_globals():
    return {
        "css": CSS,
        "config": app.config,
        "favicon_b64": FAVICON_B64,
        "ICONS": ICONS,
    }
# =============================================================
# ROUTE : CHANGER DE LANGUE
# =============================================================
@app.route("/set-lang/<code>")
def set_lang(code):
    if code in app.config["LANGUAGES"]:
        session["lang"] = code
        session.permanent = True
    resp = redirect(request.referrer or url_for("index"))
    if code in app.config["LANGUAGES"]:
        resp.set_cookie("lang", code, max_age=365*24*3600)
    return resp


# =============================================================
# AUTH CLIENT
# =============================================================
@app.route("/inscription", methods=["GET", "POST"])
def inscription():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        pwd = request.form["password"]
        pwd2 = request.form["password2"]
        nom = request.form.get("nom", "").strip()
        if pwd != pwd2:
            flash(_("passwords_dont_match"), "error")
            return redirect(url_for("inscription"))
        if Utilisateur.query.filter_by(email=email).first():
            flash(_("email_exists"), "error")
            return redirect(url_for("inscription"))
        u = Utilisateur(email=email, nom=nom)
        u.set_password(pwd)
        db.session.add(u)
        db.session.commit()
        login_user(u, remember=True)
        session.permanent = True
        flash(_("account_created"), "success")
        return redirect(url_for("mon_compte"))
    return render_template("inscription")


@app.route("/connexion", methods=["GET", "POST"])
def connexion():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        pwd = request.form["password"]
        admin_user = app.config["ADMIN_USERNAME"].lower()
        admin_email = app.config["ADMIN_EMAIL"].lower()
        if (email == admin_user or email == admin_email) and pwd == app.config["ADMIN_PASSWORD"]:
            login_user(Admin(), remember=True)
            session.permanent = True
            flash("Bienvenue dans l'admin !", "success")
            return redirect(url_for("admin_dashboard"))
        u = Utilisateur.query.filter_by(email=email).first()
        if u and u.check_password(pwd):
            login_user(u, remember=True)
            session.permanent = True
            flash(_("welcome_back"), "success")
            return redirect(url_for("mon_compte"))
        flash(_("invalid_credentials"), "error")
    return render_template("connexion")


@app.route("/deconnexion")
def deconnexion():
    logout_user()
    flash("Vous êtes déconnecté.", "info")
    return redirect(url_for("index"))


@app.route("/mon-compte")
@login_required
def mon_compte():
    return render_template("mon_compte")


# =============================================================
# ROUTES PUBLIQUES
# =============================================================
@app.route("/")
def index():
    avis = Avis.query.filter_by(valide=True).order_by(Avis.ordre.desc(), Avis.date.desc()).limit(12).all()
    tous_avis = Avis.query.filter_by(valide=True).all()
    nb_avis = len(tous_avis) if tous_avis else 0
    note_moy = round(sum(a.note for a in tous_avis) / nb_avis, 1) if nb_avis else 5.0
    slides = Slide.query.order_by(Slide.ordre).all()
    return render_template("index", avis=avis, slides=slides,
                           nb_avis=nb_avis, note_moyenne=note_moy)


@app.route("/avis", methods=["POST"])
def poster_avis():
    nom = request.form.get("nom", "").strip()[:80]
    role = request.form.get("role", "Client").strip()[:60] or "Client"
    note = int(request.form.get("note", 5))
    texte = request.form.get("texte", "").strip()[:600]
    if nom and texte:
        db.session.add(Avis(nom=nom, role=role, note=note, texte=texte, valide=True))
        db.session.commit()
        flash("Merci pour votre avis !", "success")
    return redirect(url_for("index") + "#avis")


def _liste_categorie(slug_cat, titre, sous_titre=""):
    cat = Categorie.query.filter_by(slug=slug_cat).first()
    produits = Produit.query.filter_by(actif=True, categorie_id=cat.id).order_by(Produit.id).all() if cat else []
    return render_template("categorie_liste", titre=titre, sous_titre=sous_titre, produits=produits)


@app.route("/medicaments")
def medicaments():
    return _liste_categorie("medicaments", _("meds"))


@app.route("/peptides")
def peptides():
    return _liste_categorie("peptides", _("peptides"))


@app.route("/pilules")
def pilules():
    return _liste_categorie("pilules", _("pills"))


@app.route("/recherche")
def recherche():
    q = request.args.get("q", "").strip()
    produits = Produit.query.filter(Produit.actif == True, Produit.nom.ilike(f"%{q}%")).all() if q else []
    return render_template("recherche", q=q, produits=produits)


@app.route("/produit/<slug>")
def produit_detail(slug):
    produit = Produit.query.filter_by(slug=slug, actif=True).first_or_404()
    return render_template("produit", produit=produit)


@app.route("/faq")
def faq():
    return render_template("faq", questions=FAQ.query.order_by(FAQ.ordre).all())


@app.route("/page/<slug>")
def page_dynamique(slug):
    page = Page.query.filter_by(slug=slug).first_or_404()
    return render_template("page_dynamique", page=page)


@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        db.session.add(Message(nom=request.form["nom"], email=request.form["email"], message=request.form["message"]))
        db.session.commit()
        flash(_("message_sent"), "success")
        return redirect(url_for("contact"))
    return render_template("contact")


@app.route("/blog")
def blog():
    return render_template("blog", articles=Article.query.order_by(Article.date.desc()).all())


@app.route("/blog/<slug>")
def blog_article(slug):
    article = Article.query.filter_by(slug=slug).first_or_404()
    return render_template("blog_article", article=article)


@app.route("/newsletter", methods=["POST"])
def newsletter():
    flash("Merci pour votre inscription !", "success")
    return redirect(url_for("index"))


# =============================================================
# PANIER
# =============================================================
@app.route("/panier")
def panier():
    p = get_panier()
    ids = [int(i) for i in p.keys()]
    produits = Produit.query.filter(Produit.id.in_(ids)).all() if ids else []
    items = [{"produit": prod, "quantite": p[str(prod.id)], "sous_total": prod.prix * p[str(prod.id)]} for prod in produits]
    return render_template("panier", items=items, total=total_panier())


@app.route("/panier/ajouter/<int:produit_id>", methods=["POST"])
def panier_ajouter(produit_id):
    produit = Produit.query.get_or_404(produit_id)
    qte = int(request.form.get("quantite", 1))
    p = get_panier()
    p[str(produit_id)] = p.get(str(produit_id), 0) + qte
    session.modified = True
    flash(f"{produit.nom} - {_('add_to_cart')}", "success")
    return redirect(request.referrer or url_for("index"))


@app.route("/panier/modifier/<int:produit_id>", methods=["POST"])
def panier_modifier(produit_id):
    qte = int(request.form.get("quantite", 1))
    p = get_panier()
    if qte <= 0:
        p.pop(str(produit_id), None)
    else:
        p[str(produit_id)] = qte
    session.modified = True
    return redirect(url_for("panier"))


@app.route("/panier/supprimer/<int:produit_id>")
def panier_supprimer(produit_id):
    p = get_panier()
    p.pop(str(produit_id), None)
    session.modified = True
    return redirect(url_for("panier"))


@app.route("/api/cart")
def api_cart():
    p = get_panier()
    ids = [int(i) for i in p.keys()]
    produits = Produit.query.filter(Produit.id.in_(ids)).all() if ids else []
    items = []
    for prod in produits:
        qte = p[str(prod.id)]
        items.append({
            "id": prod.id, "nom": prod.nom,
            "prix": f"{prod.prix:,.2f} €".replace(",", " ").replace(".", ","),
            "qte": qte, "image": prod.image or "",
            "sous_total": f"{prod.prix*qte:,.2f} €".replace(",", " ").replace(".", ","),
        })
    return jsonify({
        "items": items, "count": sum(p.values()),
        "total": f"{total_panier():,.2f} €".replace(",", " ").replace(".", ","),
    })


@app.route("/api/cart/update", methods=["POST"])
def api_cart_update():
    data = request.get_json() or {}
    pid = str(data.get("id"))
    qte = int(data.get("qte", 1))
    p = get_panier()
    if qte <= 0:
        p.pop(pid, None)
    else:
        p[pid] = qte
    session.modified = True
    return jsonify({"ok": True})


@app.route("/api/cart/remove", methods=["POST"])
def api_cart_remove():
    data = request.get_json() or {}
    pid = str(data.get("id"))
    p = get_panier()
    p.pop(pid, None)
    session.modified = True
    return jsonify({"ok": True})


# =============================================================
# COMMANDE : enregistre + WhatsApp
# =============================================================
@app.route("/commander", methods=["GET", "POST"])
def commander():
    if request.method == "POST":
        p = get_panier()
        if not p:
            flash(_("empty_cart"), "error")
            return redirect(url_for("panier"))

        cmd = Commande(reference=nouvelle_reference(),
                       nom_client=request.form["nom"],
                       email=request.form["email"],
                       telephone=request.form.get("telephone", ""),
                       adresse=request.form["adresse"],
                       total=total_panier())
        if current_user.is_authenticated and current_user.id != "admin":
            cmd.user_id = current_user.id
        db.session.add(cmd)
        db.session.flush()
        for pid, qte in p.items():
            prod = Produit.query.get(int(pid))
            if prod:
                db.session.add(LigneCommande(commande_id=cmd.id, produit_id=prod.id,
                                             produit_nom=prod.nom, quantite=qte,
                                             prix_unitaire=prod.prix))
        db.session.commit()

        lignes = []
        lignes.append("🛒 NOUVELLE COMMANDE " + app.config["SITE_NAME"])
        lignes.append("")
        lignes.append("Référence : " + cmd.reference)
        lignes.append("Nom : " + str(cmd.nom_client or ""))
        lignes.append("Email : " + str(cmd.email or ""))
        lignes.append("Téléphone : " + str(cmd.telephone or ""))
        lignes.append("Adresse : " + str(cmd.adresse or ""))
        lignes.append("")
        lignes.append("📦 ARTICLES :")
        for l in cmd.lignes:
            nom = l.produit_nom or (l.produit.nom if l.produit else "-")
            total_l = (l.prix_unitaire or 0) * (l.quantite or 0)
            lignes.append("- " + str(l.quantite) + "x " + str(nom) + " = " + f"{total_l:.2f}" + " €")
        lignes.append("")
        lignes.append("💰 TOTAL : " + f"{cmd.total:.2f}" + " €")
        lignes.append("")
        lignes.append("Merci de me contacter pour les détails de paiement.")

        message = "\n".join(lignes)
        session["panier"] = {}

        num = re.sub(r"\D", "", app.config["WHATSAPP_NUMBER"])
        wa_link = "https://wa.me/" + num + "?text=" + quote(message)
        return redirect(wa_link)

    p = get_panier()
    ids = [int(i) for i in p.keys()]
    produits = Produit.query.filter(Produit.id.in_(ids)).all() if ids else []
    items = [{"produit": prod, "quantite": p[str(prod.id)], "sous_total": prod.prix * p[str(prod.id)]} for prod in produits]
    return render_template("commander", items=items, total=total_panier())


# =============================================================
# ADMIN
# =============================================================
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        ident = (request.form.get("identifiant") or "").strip()
        pwd = request.form.get("password") or ""
        print(f"[ADMIN LOGIN] identifiant = '{ident}'")
        ident_low = ident.lower()
        ok_user  = (ident_low == app.config["ADMIN_USERNAME"].lower())
        ok_email = (ident_low == app.config["ADMIN_EMAIL"].lower())
        ok_pwd   = (pwd == app.config["ADMIN_PASSWORD"])
        if (ok_user or ok_email) and ok_pwd:
            login_user(Admin(), remember=True)
            session.permanent = True
            flash("Bienvenue dans l'admin !", "success")
            return redirect(url_for("admin_dashboard"))
        flash("Identifiants invalides.", "error")
    return render_template("admin_login")


@app.route("/admin/logout")
@login_required
def admin_logout():
    if current_user.is_authenticated and getattr(current_user, "id", None) == "admin":
        logout_user()
    flash("Déconnecté de l'admin.", "info")
    return redirect(url_for("admin_login"))


@app.route("/admin")
@login_required
def admin_dashboard():
    if not _admin_only():
        return redirect(url_for("admin_login"))
    stats = {
        "produits": Produit.query.count(),
        "commandes": Commande.query.count(),
        "avis": Avis.query.filter_by(valide=True).count(),
        "messages": Message.query.filter_by(lu=False).count(),
        "users": Utilisateur.query.count(),
        "pages": Page.query.count(),
        "categories": Categorie.query.count(),
        "articles": Article.query.count(),
        "slides": Slide.query.count(),
        "faq": FAQ.query.count(),
    }
    return render_template("admin_dashboard", stats=stats)


@app.route("/admin/commandes")
@login_required
def admin_commandes():
    if not _admin_only(): return redirect(url_for("admin_login"))
    statut = request.args.get("statut", "").strip()
    req = Commande.query
    if statut: req = req.filter_by(statut=statut)
    return render_template("admin_commandes", commandes=req.order_by(Commande.date.desc()).all(), statut_filtre=statut)


@app.route("/admin/commandes/<int:cid>", methods=["GET", "POST"])
@login_required
def admin_commande_detail(cid):
    if not _admin_only(): return redirect(url_for("admin_login"))
    cmd = Commande.query.get_or_404(cid)
    if request.method == "POST":
        cmd.statut = request.form.get("statut", cmd.statut)
        cmd.note = request.form.get("note", "")
        db.session.commit()
        flash("Commande mise à jour.", "success")
        return redirect(url_for("admin_commande_detail", cid=cid))
    return render_template("admin_commande_detail", commande=cmd)


@app.route("/admin/commandes/export")
@login_required
def admin_commandes_export():
    if not _admin_only(): return redirect(url_for("admin_login"))
    si = io.StringIO()
    w = csv.writer(si)
    w.writerow(["Reference", "Date", "Client", "Email", "Telephone", "Total", "Statut"])
    for c in Commande.query.order_by(Commande.date.desc()).all():
        w.writerow([c.reference, c.date.strftime("%Y-%m-%d %H:%M"), c.nom_client, c.email, c.telephone, c.total, c.statut])
    return make_response(si.getvalue(), 200, {"Content-Type": "text/csv", "Content-Disposition": "attachment; filename=commandes.csv"})


@app.route("/admin/utilisateurs")
@login_required
def admin_utilisateurs():
    if not _admin_only(): return redirect(url_for("admin_login"))
    return render_template("admin_utilisateurs", users=Utilisateur.query.order_by(Utilisateur.date_creation.desc()).all())


@app.route("/admin/utilisateurs/<int:uid>/supprimer", methods=["POST"])
@login_required
def admin_utilisateur_supprimer(uid):
    if not _admin_only(): return redirect(url_for("admin_login"))
    u = Utilisateur.query.get_or_404(uid)
    db.session.delete(u)
    db.session.commit()
    return redirect(url_for("admin_utilisateurs"))


@app.route("/admin/messages")
@login_required
def admin_messages():
    if not _admin_only(): return redirect(url_for("admin_login"))
    return render_template("admin_messages", messages=Message.query.order_by(Message.date.desc()).all())


@app.route("/admin/messages/<int:mid>/lu", methods=["POST"])
@login_required
def admin_message_lu(mid):
    if not _admin_only(): return redirect(url_for("admin_login"))
    m = Message.query.get_or_404(mid)
    m.lu = not m.lu
    db.session.commit()
    return redirect(url_for("admin_messages"))


@app.route("/admin/messages/<int:mid>/supprimer", methods=["POST"])
@login_required
def admin_message_supprimer(mid):
    if not _admin_only(): return redirect(url_for("admin_login"))
    m = Message.query.get_or_404(mid)
    db.session.delete(m)
    db.session.commit()
    return redirect(url_for("admin_messages"))


@app.route("/admin/slides", methods=["GET", "POST"])
@login_required
def admin_slides():
    if not _admin_only(): return redirect(url_for("admin_login"))
    if request.method == "POST":
        path = save_upload(request.files.get("image_file")) or request.form.get("image", "").strip()
        if path:
            db.session.add(Slide(image=path, ordre=int(request.form.get("ordre", 0))))
            db.session.commit()
            flash("Slide ajoutée.", "success")
        return redirect(url_for("admin_slides"))
    return render_template("admin_slides", slides=Slide.query.order_by(Slide.ordre).all())


@app.route("/admin/slides/<int:sid>/supprimer", methods=["POST"])
@login_required
def admin_slide_supprimer(sid):
    if not _admin_only(): return redirect(url_for("admin_login"))
    s = Slide.query.get_or_404(sid)
    db.session.delete(s)
    db.session.commit()
    return redirect(url_for("admin_slides"))


@app.route("/admin/articles")
@login_required
def admin_articles():
    if not _admin_only(): return redirect(url_for("admin_login"))
    return render_template("admin_articles", articles=Article.query.order_by(Article.date.desc()).all())


@app.route("/admin/articles/nouveau", methods=["GET", "POST"])
@app.route("/admin/articles/<int:aid>/edit", methods=["GET", "POST"])
@login_required
def admin_article_form(aid=None):
    if not _admin_only(): return redirect(url_for("admin_login"))
    article = Article.query.get(aid) if aid else Article()
    if request.method == "POST":
        article.titre = request.form["titre"]
        article.slug = slugify(article.titre)
        article.categorie = request.form.get("categorie", "Blog")
        article.extrait = request.form.get("extrait", "")
        article.contenu = request.form.get("contenu", "")
        path = save_upload(request.files.get("image_file"))
        article.image = path if path else request.form.get("image", "")
        if not aid: db.session.add(article)
        db.session.commit()
        flash("Article enregistré.", "success")
        return redirect(url_for("admin_articles"))
    return render_template("admin_article_form", article=article)


@app.route("/admin/articles/<int:aid>/supprimer", methods=["POST"])
@login_required
def admin_article_supprimer(aid):
    if not _admin_only(): return redirect(url_for("admin_login"))
    a = Article.query.get_or_404(aid)
    db.session.delete(a)
    db.session.commit()
    return redirect(url_for("admin_articles"))


@app.route("/admin/contenu", methods=["GET", "POST"])
@login_required
def admin_contenu():
    if not _admin_only(): return redirect(url_for("admin_login"))
    cles = ["hero_image", "hero_badge", "hero_titre", "hero_texte", "hero_btn_texte", "hero_btn_lien",
            "feat1", "feat2", "feat3", "feat4",
            "about_image", "about_titre", "about_texte",
            "violet_titre", "violet_p1a", "violet_p1b", "violet_p2a", "violet_p2b"]
    if request.method == "POST":
        for field, cle in [("hero_image_file", "hero_image"), ("about_image_file", "about_image")]:
            path = save_upload(request.files.get(field))
            if path:
                c = Contenu.query.filter_by(cle=cle).first()
                if c: c.valeur = path
                else: db.session.add(Contenu(cle=cle, valeur=path))
        for cle in cles:
            val = request.form.get(cle, "")
            c = Contenu.query.filter_by(cle=cle).first()
            if c:
                if val: c.valeur = val
            elif val:
                db.session.add(Contenu(cle=cle, valeur=val))
        db.session.commit()
        flash("Contenu enregistré.", "success")
        return redirect(url_for("admin_contenu"))
    return render_template("admin_contenu", c={cle: get_contenu(cle, "") for cle in cles})


@app.route("/admin/produits")
@login_required
def admin_produits():
    if not _admin_only(): return redirect(url_for("admin_login"))
    return render_template("admin_produits", produits=Produit.query.order_by(Produit.id.desc()).all())


@app.route("/admin/produits/nouveau", methods=["GET", "POST"])
@app.route("/admin/produits/<int:pid>/edit", methods=["GET", "POST"])
@login_required
def admin_produit_form(pid=None):
    if not _admin_only(): return redirect(url_for("admin_login"))
    produit = Produit.query.get(pid) if pid else Produit()
    categories = Categorie.query.all()
    if request.method == "POST":
        produit.nom = request.form["nom"]
        produit.slug = slugify(produit.nom)
        produit.sous_titre = request.form.get("sous_titre", "")
        produit.description = request.form["description"]
        produit.prix = float(request.form["prix"])
        produit.prix_max = float(request.form.get("prix_max", 0) or 0)
        produit.stock = int(request.form["stock"])
        path = save_upload(request.files.get("image_file"))
        produit.image = path if path else request.form.get("image", "")
        produit.categorie_id = request.form.get("categorie_id") or None
        produit.actif = "actif" in request.form
        if not pid: db.session.add(produit)
        db.session.commit()
        flash("Produit enregistré.", "success")
        return redirect(url_for("admin_produits"))
    return render_template("admin_produit_form", produit=produit, categories=categories)


@app.route("/admin/produits/<int:pid>/supprimer", methods=["POST"])
@login_required
def admin_produit_supprimer(pid):
    if not _admin_only(): return redirect(url_for("admin_login"))
    p = Produit.query.get_or_404(pid)
    # supprimer les fichiers photos
    for photo in p.photos:
        try:
            fp = os.path.join(app.config["UPLOAD_FOLDER"], os.path.basename(photo.chemin))
            if os.path.exists(fp): os.remove(fp)
        except Exception:
            pass
    db.session.delete(p)
    db.session.commit()
    return redirect(url_for("admin_produits"))


# =============================================================
# ADMIN — GESTION GALERIE PHOTOS PRODUIT
# =============================================================
@app.route("/admin/produits/<int:pid>/photos", methods=["GET"])
@login_required
def admin_produit_photos(pid):
    if not _admin_only(): return redirect(url_for("admin_login"))
    produit = Produit.query.get_or_404(pid)
    return render_template("admin_produit_photos", produit=produit)


@app.route("/admin/produits/<int:pid>/photos/upload", methods=["POST"])
@login_required
def admin_produit_photo_upload(pid):
    if not _admin_only(): return redirect(url_for("admin_login"))
    produit = Produit.query.get_or_404(pid)
    files = request.files.getlist("photos")
    deja = produit.photos.count() if hasattr(produit.photos, "count") else len(produit.photos)
    slots_libres = MAX_PHOTOS_PAR_PRODUIT - deja
    if slots_libres <= 0:
        flash(f"Maximum {MAX_PHOTOS_PAR_PRODUIT} photos déjà atteint.", "error")
        return redirect(url_for("admin_produit_photos", pid=pid))
    ordre = deja
    ajoutees = 0
    for f in files:
        if ajoutees >= slots_libres: break
        path = save_upload(f)
        if path:
            db.session.add(PhotoProduit(produit_id=produit.id, chemin=path, ordre=ordre))
            ordre += 1
            ajoutees += 1
    if ajoutees > 0:
        db.session.commit()
        flash(f"{ajoutees} photo(s) ajoutée(s).", "success")
    else:
        flash("Aucune photo valide.", "error")
    return redirect(url_for("admin_produit_photos", pid=pid))


@app.route("/admin/produits/<int:pid>/photos/<int:photo_id>/supprimer", methods=["POST"])
@login_required
def admin_produit_photo_supprimer(pid, photo_id):
    if not _admin_only(): return redirect(url_for("admin_login"))
    photo = PhotoProduit.query.get_or_404(photo_id)
    if photo.produit_id != pid:
        return redirect(url_for("admin_produits"))
    # supprimer le fichier
    try:
        fp = os.path.join(app.config["UPLOAD_FOLDER"], os.path.basename(photo.chemin))
        if os.path.exists(fp): os.remove(fp)
    except Exception:
        pass
    db.session.delete(photo)
    db.session.commit()
    flash("Photo supprimée.", "success")
    return redirect(url_for("admin_produit_photos", pid=pid))


@app.route("/admin/categories", methods=["GET", "POST"])
@login_required
def admin_categories():
    if not _admin_only(): return redirect(url_for("admin_login"))
    if request.method == "POST":
        nom = request.form["nom"]
        db.session.add(Categorie(nom=nom, slug=slugify(nom), ordre=int(request.form.get("ordre", 0))))
        db.session.commit()
        return redirect(url_for("admin_categories"))
    return render_template("admin_categories", categories=Categorie.query.order_by(Categorie.ordre).all())


@app.route("/admin/categories/<int:cid>/supprimer", methods=["POST"])
@login_required
def admin_categorie_supprimer(cid):
    if not _admin_only(): return redirect(url_for("admin_login"))
    c = Categorie.query.get_or_404(cid)
    db.session.delete(c)
    db.session.commit()
    return redirect(url_for("admin_categories"))


@app.route("/admin/pages")
@login_required
def admin_pages():
    if not _admin_only(): return redirect(url_for("admin_login"))
    return render_template("admin_pages", pages=Page.query.order_by(Page.ordre).all())


@app.route("/admin/pages/nouvelle", methods=["GET", "POST"])
@app.route("/admin/pages/<int:pid>/edit", methods=["GET", "POST"])
@login_required
def admin_page_form(pid=None):
    if not _admin_only(): return redirect(url_for("admin_login"))
    page = Page.query.get(pid) if pid else Page()
    if request.method == "POST":
        page.titre = request.form["titre"]
        s = request.form.get("slug", "").strip()
        page.slug = s if s else slugify(page.titre)
        page.contenu = request.form["contenu"]
        page.ordre = int(request.form.get("ordre", 0))
        page.afficher_menu = "afficher_menu" in request.form
        if not pid: db.session.add(page)
        db.session.commit()
        return redirect(url_for("admin_pages"))
    return render_template("admin_page_form", page=page)


@app.route("/admin/pages/<int:pid>/supprimer", methods=["POST"])
@login_required
def admin_page_supprimer(pid):
    if not _admin_only(): return redirect(url_for("admin_login"))
    pg = Page.query.get_or_404(pid)
    db.session.delete(pg)
    db.session.commit()
    return redirect(url_for("admin_pages"))


@app.route("/admin/avis", methods=["GET", "POST"])
@login_required
def admin_avis():
    if not _admin_only(): return redirect(url_for("admin_login"))
    if request.method == "POST":
        db.session.add(Avis(nom=request.form["nom"], role=request.form.get("role", "Client"),
                            note=int(request.form.get("note", 5)), texte=request.form["texte"],
                            valide="valide" in request.form))
        db.session.commit()
        return redirect(url_for("admin_avis"))
    return render_template("admin_avis", avis=Avis.query.order_by(Avis.date.desc()).all())


@app.route("/admin/avis/<int:aid>/supprimer", methods=["POST"])
@login_required
def admin_avis_supprimer(aid):
    if not _admin_only(): return redirect(url_for("admin_login"))
    a = Avis.query.get_or_404(aid)
    db.session.delete(a)
    db.session.commit()
    return redirect(url_for("admin_avis"))


@app.route("/admin/avis/<int:aid>/toggle", methods=["POST"])
@login_required
def admin_avis_toggle(aid):
    if not _admin_only(): return redirect(url_for("admin_login"))
    a = Avis.query.get_or_404(aid)
    a.valide = not a.valide
    db.session.commit()
    return redirect(url_for("admin_avis"))


@app.route("/admin/faq", methods=["GET", "POST"])
@login_required
def admin_faq():
    if not _admin_only(): return redirect(url_for("admin_login"))
    if request.method == "POST":
        db.session.add(FAQ(question=request.form["question"], reponse=request.form["reponse"]))
        db.session.commit()
        return redirect(url_for("admin_faq"))
    return render_template("admin_faq", questions=FAQ.query.order_by(FAQ.ordre).all())


@app.route("/admin/faq/<int:fid>/supprimer", methods=["POST"])
@login_required
def admin_faq_supprimer(fid):
    if not _admin_only(): return redirect(url_for("admin_login"))
    f = FAQ.query.get_or_404(fid)
    db.session.delete(f)
    db.session.commit()
    return redirect(url_for("admin_faq"))


# =============================================================
# ERREURS
# =============================================================
@app.errorhandler(404)
def not_found(e):
    return render_template("404"), 404


@app.errorhandler(500)
def server_error(e):
    return render_template("404"), 500


# =============================================================
# SEED — Données initiales
# =============================================================
def seed():
    try:
        db.create_all()

        cats = {"peptides": "Peptides", "medicaments": "Médicaments", "pilules": "Pilules pour l'érection"}
        for slug, nom in cats.items():
            if not Categorie.query.filter_by(slug=slug).first():
                db.session.add(Categorie(nom=nom, slug=slug))
        db.session.commit()

        cat_med = Categorie.query.filter_by(slug="medicaments").first()
        cat_pep = Categorie.query.filter_by(slug="peptides").first()
        cat_pil = Categorie.query.filter_by(slug="pilules").first()

        if not Slide.query.first():
            for i, img in enumerate([
                "https://images.unsplash.com/photo-1534438327276-14e5300c3a48?w=1600",
                "https://images.unsplash.com/photo-1517836357463-d25dfeac3438?w=1600",
                "https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b?w=1600",
                "https://images.unsplash.com/photo-1518611012118-696072aa579a?w=1600",
                "https://images.unsplash.com/photo-1552674605-db6ffd4facb5?w=1600",
            ]):
                db.session.add(Slide(image=img, ordre=i))

        defauts = {
            "hero_image": "https://images.unsplash.com/photo-1534438327276-14e5300c3a48?w=1600",
            "hero_badge": "Bienvenue dans la boutique Monjaroo",
            "hero_titre": "Produits de bien-être haut de gamme pour la santé quotidienne",
            "hero_texte": "Découvrez des compléments alimentaires et produits de bien-être de qualité supérieure, rigoureusement testés et approuvés.",
            "hero_btn_texte": "Achetez maintenant", "hero_btn_lien": "/peptides",
            "feat1": "Magasin fiable proposant des produits de qualité.",
            "feat2": "Des prix abordables et attractifs pour tous les clients.",
            "feat3": "Livraison express gratuite avec suivi.",
            "feat4": "Assistance en ligne 24h/24 et 7j/7.",
            "about_image": "https://images.unsplash.com/photo-1571019614242-c5c5dee9f50b?w=900",
            "about_titre": "Promouvoir la santé par la qualité et les soins",
            "about_texte": "Chez Monjaroo.shop, nous croyons que la véritable santé commence par la confiance.",
            "violet_titre": "Découvrez nos peptides et médicaments",
            "violet_p1a": "L'innovation commence par de bonnes bases.",
            "violet_p1b": "Nos peptides sont conçus pour la recherche de pointe.",
            "violet_p2a": "Vous achetez des médicaments en ligne ?",
            "violet_p2b": "Commandez facilement et en toute fiabilité.",
        }
        for k, v in defauts.items():
            if not Contenu.query.filter_by(cle=k).first():
                db.session.add(Contenu(cle=k, valeur=v))

        if cat_med and not Produit.query.filter_by(categorie_id=cat_med.id).first():
            for nom, sous, pm, px in [
                ("Diazépam 10 mg, pot de 100 compresses", "diazepam", 149.95, 0),
                ("Alprazolam 2 mg BARZ (XANAX) 60 compresses", "alprazolam", 109.95, 0),
                ("Ozempic 1 mg", "ozempic", 189.95, 0),
                ("Témazépam 20 mg", "temazepam", 29.95, 79.95),
                ("Montjaro", "montjaro", 239.95, 449.95),
                ("Lorazépam 2,5 mg", "lorazepam", 24.95, 59.95),
                ("Zolpidem 10 mg", "zolpidem", 24.95, 59.95),
                ("Tramadol 50 mg", "tramadol", 22.95, 54.95),
                ("Alprazolam (Xanax 1 mg)", "alprazolam-xanax", 24.95, 59.95),
                ("Oxazépam 10 mg", "oxazepam", 24.95, 59.95),
                ("Clonazépam 2 mg", "ivotril", 21.95, 49.95),
                ("Ritaline 10 mg", "methylphenidate", 23.95, 59.95),
                ("Citalopram 20 mg", "citalopram", 21.95, 54.95),
                ("Bromazépam HF 6 mg", "bromazepam", 29.95, 59.95),
                ("Midazolam 15 mg", "midazolam", 24.95, 69.95),
                ("Diazépam 10 mg", "diazepam-10", 21.95, 54.95),
            ]:
                db.session.add(Produit(nom=nom, slug=slugify(nom + "-" + sous), sous_titre=sous,
                                       prix=pm, prix_max=px, stock=30, categorie_id=cat_med.id, actif=True))

        if cat_pep and not Produit.query.filter_by(categorie_id=cat_pep.id).first():
            for nom, sous, prix in [
                ("Tirzapetide 40 mg", "tirzepatide", 209.95),
                ("Tirzapetide 20 mg", "tirzepatide", 159.95),
                ("BPC-157 et TB-500 / 40 mg", "bpci57-tb500", 159.95),
                ("NAD+ 1000 mg", "nad", 179.95),
                ("GLOW GHK CU 70MG", "glow-ghk-cu", 159.95),
                ("Rétatrutide 20 mg", "retatrutide", 179.95),
                ("Rétatrutide 40 mg", "retatrutide-40", 279.95),
            ]:
                db.session.add(Produit(nom=nom, slug=slugify(nom + "-" + sous), sous_titre=sous,
                                       prix=prix, stock=20, categorie_id=cat_pep.id, actif=True))

        if cat_pil and not Produit.query.filter_by(categorie_id=cat_pil.id).first():
            for nom, sous, prix in [
                ("Lovegra 100 mg", "Lovegra", 9.95),
                ("Gelée de Kamagra", "gele-kamagra", 16.95),
                ("Vidalista 60 mg", "Vidalista", 16.95),
                ("Cenforce 200 mg", "Cenforce", 17.49),
                ("Kamagra 100 mg", "Kamagra-100", 8.95),
                ("Cobra 120 mg", "cobra-120", 14.95),
            ]:
                db.session.add(Produit(nom=nom, slug=slugify(nom + "-" + sous), sous_titre=sous,
                                       prix=prix, stock=50, categorie_id=cat_pil.id, actif=True))

        pages = {
            "conditions-generales": ("Conditions générales", "<h2>1. Objet</h2><p>Les présentes conditions régissent l'utilisation du site Monjaroo.shop.</p><h2>2. Produits</h2><p>Tous les produits sont destinés à un usage strictement personnel et légal.</p><h2>3. Commande</h2><p>Toute commande implique l'acceptation sans réserve des présentes conditions.</p><h2>4. Prix et paiement</h2><p>Les prix sont indiqués en euros, toutes taxes comprises.</p><h2>5. Livraison</h2><p>Les produits sont expédiés dans un emballage neutre et discret sous 3 à 10 jours ouvrés.</p>"),
            "retours-remboursements": ("Retours et remboursements", "<h2>1. Politique de retour</h2><p>Vous disposez de 14 jours à compter de la réception pour demander un retour.</p><h2>2. Conditions</h2><ul><li>Emballage d'origine non ouvert</li><li>Produits pharmaceutiques non repris</li></ul><h2>3. Procédure</h2><p>Contactez-nous à info@monjaroo.shop ou par WhatsApp.</p><h2>4. Remboursement</h2><p>Sous 14 jours sur le moyen de paiement d'origine.</p>"),
            "politique-confidentialite": ("Politique de confidentialité", "<h2>1. Données collectées</h2><p>Uniquement les données nécessaires au traitement des commandes.</p><h2>2. Utilisation</h2><p>Traitement des commandes et suivi.</p><h2>3. Partage</h2><p>Vos données ne sont jamais vendues.</p><h2>4. Cookies</h2><p>Cookies techniques et analytiques anonymes.</p><h2>5. Vos droits (RGPD)</h2><p>Écrivez à info@monjaroo.shop.</p>"),
        }
        for slug, (titre, contenu) in pages.items():
            if not Page.query.filter_by(slug=slug).first():
                db.session.add(Page(titre=titre, slug=slug, contenu=contenu, afficher_menu=False))

        if not FAQ.query.first():
            db.session.add_all([
                FAQ(question="Quels produits propose la boutique Monjaroo ?",
                    reponse="Nous proposons une large gamme de produits de bien-être : peptides, médicaments et pilules.", ordre=1),
                FAQ(question="Vos produits sont-ils sûrs et homologués ?",
                    reponse="Tous nos produits proviennent de fournisseurs de confiance.", ordre=2),
                FAQ(question="Combien de temps prend la livraison ?",
                    reponse="1 à 2 jours ouvrés de traitement. Livraison 3-7 jours.", ordre=3),
                FAQ(question="Proposez-vous la livraison internationale ?",
                    reponse="Oui, dans la plupart des pays européens et internationalement.", ordre=4),
                FAQ(question="Quels modes de paiement acceptez-vous ?",
                    reponse="Carte bancaire, virement. Contactez-nous par WhatsApp.", ordre=5),
                FAQ(question="Puis-je retourner ou échanger ma commande ?",
                    reponse="Retours uniquement en cas d'erreur de notre part.", ordre=6),
                FAQ(question="Comment puis-je contacter le service client ?",
                    reponse="WhatsApp, info@monjaroo.shop, ou +33 6 44 69 06 92.", ordre=7),
                FAQ(question="Vos compléments conviennent-ils à tout le monde ?",
                    reponse="Usage adulte. Consultez un médecin en cas de doute.", ordre=8),
                FAQ(question="Comment conserver mes produits ?",
                    reponse="Endroit sec, à l'abri de la lumière, 15-25°C.", ordre=9),
            ])

        if not Avis.query.first():
            prenoms = ["Daniel R.", "Saar B.", "Dennis W.", "Marie L.", "Julien K.", "Sophie M.", "Antoine D.", "Camille B.", "Lucas P.", "Emma T.",
                       "Hugo V.", "Léa R.", "Nathan G.", "Chloé F.", "Maxime H.", "Manon S.", "Théo J.", "Sarah N.", "Alexandre C.", "Inès B.",
                       "Paul M.", "Alice D.", "Romain P.", "Julie L.", "Kevin Z.", "Amélie V.", "Baptiste Q.", "Élodie R.", "Yanis T.", "Clara S.",
                       "Florian B.", "Nadia K.", "Mathieu L.", "Océane D.", "Adrien F.", "Noémie G.", "Simon P.", "Charlotte M.", "Damien R.", "Laetitia A.",
                       "Guillaume B.", "Sabrina H.", "Loïc V.", "Émilie P.", "Sébastien T.", "Aurélie M.", "Vincent L.", "Anaïs D.", "Cédric N.", "Marine S.",
                       "David K.", "Céline R.", "Benoît C.", "Hélène B.", "Fabien P.", "Alicia V.", "Cyril M.", "Justine L.", "Killian T.", "Louise F.",
                       "Morgan R.", "Éva G.", "Damien S.", "Pauline B.", "Raphaël D.", "Sonia M.", "Grégoire P.", "Nina T.", "Étienne L.", "Charlotte D.",
                       "Quentin F.", "Margot R.", "Thibaut B.", "Amandine V.", "Gaël S.", "Cassandre M.", "Jérôme P.", "Alix D.", "Bruno T.", "Cassie R."]
            textes = [
                "Produits de qualité, livraison rapide et discrète.",
                "Excellente communication, colis bien emballé.",
                "Rapport qualité/prix imbattable, je recommande.",
                "Site très clair, commande simple, livraison rapide.",
                "Produits conformes à mes attentes.",
                "Service client réactif par WhatsApp, parfait.",
            ]
            for i, prenom in enumerate(prenoms[:80]):
                db.session.add(Avis(nom=prenom,
                                    role="Client" if i % 4 else "Client vérifié",
                                    note=5 if i % 8 else 4,
                                    texte=textes[i % len(textes)], ordre=i, valide=True))

        if not Article.query.first():
            db.session.add_all([
                Article(titre="Que sont les peptides ?", slug="que-sont-les-peptides",
                        categorie="blog peptides",
                        extrait="Les peptides sont de courtes chaînes d'acides aminés...",
                        contenu="<p>Les peptides sont de courtes chaînes d'acides aminés.</p>",
                        date=datetime(2026, 1, 22)),
                Article(titre="Acheter des médicaments en ligne : sûr, discret et fiable",
                        slug="acheter-medicaments-en-ligne", categorie="Médicament",
                        extrait="De plus en plus de personnes achètent leurs médicaments en ligne...",
                        contenu="<p>Acheter en ligne est pratique, discret et sécurisé.</p>",
                        date=datetime(2025, 12, 28)),
                Article(titre="Que sont les peptides et pourquoi sont-ils populaires ?",
                        slug="pourquoi-peptides-populaires", categorie="peptides",
                        extrait="Les peptides connaissent une popularité croissante...",
                        contenu="<p>Les peptides sont de plus en plus étudiés.</p>",
                        date=datetime(2025, 12, 4)),
            ])

        db.session.commit()
        print(">>> SEED OK <<<")

    except Exception as e:
        print(f">>> SEED ERREUR: {e} <<<")
        import traceback
        traceback.print_exc()


# =============================================================
# INITIALISATION AU DEMARRAGE (pour Render/gunicorn)
# =============================================================
with app.app_context():
    try:
        seed()
    except Exception as e:
        print(f">>> INIT SEED ERREUR: {e} <<<")


# =============================================================
# POINT D'ENTRÉE LOCAL
# =============================================================
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
