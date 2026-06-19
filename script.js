// Mobile Navigation
const hamburger = document.querySelector('.hamburger');
const navMenu = document.querySelector('.nav-menu');

hamburger.addEventListener('click', () => {
    hamburger.classList.toggle('active');
    navMenu.classList.toggle('active');
});

// Close mobile menu when clicking on a link
document.querySelectorAll('.nav-link').forEach(n => n.addEventListener('click', () => {
    hamburger.classList.remove('active');
    navMenu.classList.remove('active');
}));

// Smooth scrolling for navigation links
function scrollToSection(sectionId) {
    const element = document.getElementById(sectionId);
    if (element) {
        element.scrollIntoView({
            behavior: 'smooth',
            block: 'start'
        });
    }
}

// Product filtering
const filterButtons = document.querySelectorAll('.filter-btn');
const productCards = document.querySelectorAll('.product-card');

filterButtons.forEach(button => {
    button.addEventListener('click', () => {
        // Remove active class from all buttons
        filterButtons.forEach(btn => btn.classList.remove('active'));
        // Add active class to clicked button
        button.classList.add('active');
        
        const category = button.getAttribute('data-category');
        
        productCards.forEach(card => {
            if (category === 'all' || card.getAttribute('data-category') === category) {
                card.style.display = 'block';
                card.style.animation = 'fadeIn 0.5s ease';
            } else {
                card.style.display = 'none';
            }
        });
    });
});

// Product details modal
const modal = document.getElementById('productModal');
const modalContent = document.getElementById('modalContent');
const closeModal = document.querySelector('.close');

// Product data
const productDetails = {
    'z790-master': {
        name: 'Gigabyte Z790 AORUS MASTER',
        price: 'R$ 4.250,00',
        image: 'https://via.placeholder.com/400x300/1e40af/ffffff?text=Z790+AORUS+MASTER',
        specs: {
            socket: 'Intel LGA 1700',
            chipset: 'Intel Z790',
            memory: '4x DDR5 DIMM, até 128GB',
            memorySpeed: 'DDR5-8000+ (OC)',
            expansion: '4x PCIe 5.0 x16, 1x PCIe 4.0 x16',
            storage: '5x M.2 (PCIe 5.0/4.0)',
            vrm: '20+1+2 Fases VRM Digital',
            connectivity: 'Wi-Fi 6E, Bluetooth 5.3, 10GbE LAN',
            audio: 'ALC1220-VB HD Audio',
            usb: '2x USB 3.2 Gen2x2 Type-C, 8x USB 3.2 Gen2 Type-A'
        },
        compatibility: [
            'Intel Core i9-14900K/KF',
            'Intel Core i7-14700K/KF', 
            'Intel Core i5-14600K/KF',
            'Intel Core i9-13900K/KF',
            'Intel Core i7-13700K/KF',
            'Intel Core i5-13600K/KF',
            'Intel Core i9-12900K/KF',
            'Intel Core i7-12700K/KF',
            'Intel Core i5-12600K/KF'
        ]
    },
    'x670e-master': {
        name: 'Gigabyte X670E AORUS MASTER',
        price: 'R$ 3.750,00',
        image: 'https://via.placeholder.com/400x300/dc2626/ffffff?text=X670E+AORUS+MASTER',
        specs: {
            socket: 'AMD AM5',
            chipset: 'AMD X670E',
            memory: '4x DDR5 DIMM, até 128GB',
            memorySpeed: 'DDR5-6666+ (OC)',
            expansion: '2x PCIe 5.0 x16, 1x PCIe 4.0 x16',
            storage: '4x M.2 (PCIe 5.0)',
            vrm: '16+2+2 Fases VRM Digital',
            connectivity: 'Wi-Fi 6E, Bluetooth 5.3, 2.5GbE LAN',
            audio: 'ALC1220-VB HD Audio',
            usb: '2x USB 3.2 Gen2x2 Type-C, 10x USB 3.2 Gen2 Type-A'
        },
        compatibility: [
            'AMD Ryzen 9 7950X',
            'AMD Ryzen 9 7900X',
            'AMD Ryzen 7 7800X3D',
            'AMD Ryzen 7 7700X',
            'AMD Ryzen 5 7600X',
            'AMD Ryzen 9 7950X3D',
            'AMD Ryzen 9 7900X3D'
        ]
    },
    'b760-elite': {
        name: 'Gigabyte B760 AORUS ELITE AX',
        price: 'R$ 1.600,00',
        image: 'https://via.placeholder.com/400x300/059669/ffffff?text=B760+AORUS+ELITE',
        specs: {
            socket: 'Intel LGA 1700',
            chipset: 'Intel B760',
            memory: '4x DDR4 DIMM, até 128GB',
            memorySpeed: 'DDR4-5333 (OC)',
            expansion: '1x PCIe 4.0 x16, 2x PCIe 3.0 x16',
            storage: '2x M.2 (PCIe 4.0)',
            vrm: '12+1+1 Fases VRM Digital',
            connectivity: 'Wi-Fi 6, Bluetooth 5.3, 2.5GbE LAN',
            audio: 'Realtek ALC897 HD Audio',
            usb: '1x USB 3.2 Gen2x2 Type-C, 6x USB 3.2 Gen1 Type-A'
        },
        compatibility: [
            'Intel Core i9-14900/14900F',
            'Intel Core i7-14700/14700F',
            'Intel Core i5-14400/14400F',
            'Intel Core i9-13900/13900F',
            'Intel Core i7-13700/13700F',
            'Intel Core i5-13400/13400F',
            'Intel Core i3-13100/13100F'
        ]
    },
    'b650-elite': {
        name: 'Gigabyte B650 AORUS ELITE AX',
        price: 'R$ 2.000,00',
        image: 'https://via.placeholder.com/400x300/7c3aed/ffffff?text=B650+AORUS+ELITE',
        specs: {
            socket: 'AMD AM5',
            chipset: 'AMD B650',
            memory: '4x DDR5 DIMM, até 128GB',
            memorySpeed: 'DDR5-6666+ (OC)',
            expansion: '1x PCIe 4.0 x16, 2x PCIe 3.0 x16',
            storage: '2x M.2 (PCIe 4.0)',
            vrm: '12+2+1 Fases VRM Digital',
            connectivity: 'Wi-Fi 6E, Bluetooth 5.3, 2.5GbE LAN',
            audio: 'Realtek ALC897 HD Audio',
            usb: '1x USB 3.2 Gen2x2 Type-C, 8x USB 3.2 Gen1 Type-A'
        },
        compatibility: [
            'AMD Ryzen 9 7900X',
            'AMD Ryzen 7 7800X3D',
            'AMD Ryzen 7 7700X',
            'AMD Ryzen 5 7600X',
            'AMD Ryzen 5 7500F'
        ]
    },
    'h610m-h': {
        name: 'Gigabyte H610M H DDR4',
        price: 'R$ 750,00',
        image: 'https://via.placeholder.com/400x300/0891b2/ffffff?text=H610M+H+DDR4',
        specs: {
            socket: 'Intel LGA 1700',
            chipset: 'Intel H610',
            memory: '2x DDR4 DIMM, até 64GB',
            memorySpeed: 'DDR4-3200',
            expansion: '1x PCIe 4.0 x16',
            storage: '1x M.2 (PCIe 3.0)',
            vrm: '6+1+1 Fases VRM Digital',
            connectivity: 'Gigabit LAN',
            audio: 'Realtek ALC887 HD Audio',
            usb: '4x USB 3.2 Gen1 Type-A, 2x USB 2.0'
        },
        compatibility: [
            'Intel Core i5-13400/13400F',
            'Intel Core i3-13100/13100F',
            'Intel Core i5-12400/12400F',
            'Intel Core i3-12100/12100F',
            'Intel Pentium Gold G7400',
            'Intel Celeron G6900'
        ]
    },
    'a520m-ds3h': {
        name: 'Gigabyte A520M DS3H',
        price: 'R$ 650,00',
        image: 'https://via.placeholder.com/400x300/ea580c/ffffff?text=A520M+DS3H',
        specs: {
            socket: 'AMD AM4',
            chipset: 'AMD A520',
            memory: '4x DDR4 DIMM, até 128GB',
            memorySpeed: 'DDR4-4733 (OC)',
            expansion: '1x PCIe 3.0 x16, 2x PCIe 3.0 x1',
            storage: '1x M.2 (PCIe 3.0)',
            vrm: '5+3 Fases VRM Digital',
            connectivity: 'Gigabit LAN',
            audio: 'Realtek ALC887 HD Audio',
            usb: '6x USB 3.2 Gen1 Type-A, 2x USB 2.0'
        },
        compatibility: [
            'AMD Ryzen 5 5600G',
            'AMD Ryzen 5 5500',
            'AMD Ryzen 3 5300G',
            'AMD Ryzen 5 3600',
            'AMD Ryzen 3 3300X',
            'AMD Ryzen 3 3200G'
        ]
    },
    'h410m-h': {
        name: 'Gigabyte H410M H V2',
        price: 'R$ 575,00',
        image: 'https://via.placeholder.com/400x300/16a34a/ffffff?text=H410M+H+V2',
        specs: {
            socket: 'Intel LGA 1200',
            chipset: 'Intel H410',
            memory: '2x DDR4 DIMM, até 64GB',
            memorySpeed: 'DDR4-2933',
            expansion: '1x PCIe 3.0 x16',
            storage: 'SATA 6Gb/s',
            vrm: '4+2 Fases VRM Digital',
            connectivity: 'Gigabit LAN',
            audio: 'Realtek ALC887 HD Audio',
            usb: '4x USB 3.2 Gen1 Type-A, 2x USB 2.0'
        },
        compatibility: [
            'Intel Core i5-10400/10400F',
            'Intel Core i3-10100/10100F',
            'Intel Pentium Gold G6400',
            'Intel Celeron G5900'
        ]
    },
    'b450m-gaming': {
        name: 'Gigabyte B450M GAMING',
        price: 'R$ 675,00',
        image: 'https://via.placeholder.com/400x300/be123c/ffffff?text=B450M+GAMING',
        specs: {
            socket: 'AMD AM4',
            chipset: 'AMD B450',
            memory: '4x DDR4 DIMM, até 64GB',
            memorySpeed: 'DDR4-3600 (OC)',
            expansion: '1x PCIe 3.0 x16, 2x PCIe 3.0 x1',
            storage: '1x M.2 (PCIe 3.0), 4x SATA 6Gb/s',
            vrm: '4+2 Fases VRM Digital',
            connectivity: 'Gigabit LAN',
            audio: 'Realtek ALC887 HD Audio',
            usb: '6x USB 3.1 Gen1 Type-A, 2x USB 2.0'
        },
        compatibility: [
            'AMD Ryzen 5 5600X',
            'AMD Ryzen 5 3600',
            'AMD Ryzen 3 3300X',
            'AMD Ryzen 5 2600',
            'AMD Ryzen 3 2200G',
            'AMD Athlon 3000G'
        ]
    }
};

function showProductDetails(productId) {
    const product = productDetails[productId];
    if (!product) return;

    const modalHTML = `
        <h2>${product.name}</h2>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 2rem; margin: 2rem 0;">
            <div>
                <img src="${product.image}" alt="${product.name}" style="width: 100%; border-radius: 10px;">
                <div style="text-align: center; margin-top: 1rem;">
                    <span style="font-size: 2rem; font-weight: bold; color: #1e40af;">${product.price}</span>
                </div>
            </div>
            <div>
                <h3 style="color: #1e40af; margin-bottom: 1rem;">Especificações Técnicas</h3>
                <div style="display: grid; gap: 0.5rem;">
                    <div><strong>Socket:</strong> ${product.specs.socket}</div>
                    <div><strong>Chipset:</strong> ${product.specs.chipset}</div>
                    <div><strong>Memória:</strong> ${product.specs.memory}</div>
                    <div><strong>Velocidade:</strong> ${product.specs.memorySpeed}</div>
                    <div><strong>Expansão:</strong> ${product.specs.expansion}</div>
                    <div><strong>Armazenamento:</strong> ${product.specs.storage}</div>
                    <div><strong>VRM:</strong> ${product.specs.vrm}</div>
                    <div><strong>Conectividade:</strong> ${product.specs.connectivity}</div>
                    <div><strong>Áudio:</strong> ${product.specs.audio}</div>
                    <div><strong>USB:</strong> ${product.specs.usb}</div>
                </div>
            </div>
        </div>
        <div>
            <h3 style="color: #1e40af; margin-bottom: 1rem;">Processadores Compatíveis</h3>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 0.5rem;">
                ${product.compatibility.map(cpu => `
                    <div style="background: #f8fafc; padding: 0.5rem; border-radius: 5px; font-size: 0.9rem;">
                        ${cpu}
                    </div>
                `).join('')}
            </div>
        </div>
        <div style="margin-top: 2rem; text-align: center;">
            <button style="background: linear-gradient(45deg, #1e40af, #3b82f6); color: white; border: none; padding: 1rem 2rem; border-radius: 10px; font-size: 1.1rem; font-weight: 600; cursor: pointer;" onclick="addToCart('${productId}')">
                <i class="fas fa-shopping-cart"></i> Adicionar ao Carrinho
            </button>
        </div>
    `;

    modalContent.innerHTML = modalHTML;
    modal.style.display = 'block';
}

function addToCart(productId) {
    alert('Produto adicionado ao carrinho! Em breve implementaremos o sistema de compras completo.');
    modal.style.display = 'none';
}

// Close modal
closeModal.addEventListener('click', () => {
    modal.style.display = 'none';
});

window.addEventListener('click', (e) => {
    if (e.target === modal) {
        modal.style.display = 'none';
    }
});

// Scroll animations
const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add('loaded');
        }
    });
}, observerOptions);

// Observe all sections for animations
document.addEventListener('DOMContentLoaded', () => {
    const sections = document.querySelectorAll('section');
    sections.forEach(section => {
        section.classList.add('loading');
        observer.observe(section);
    });

    // Add loading animation to product cards
    const cards = document.querySelectorAll('.product-card, .payment-card, .detail-card');
    cards.forEach((card, index) => {
        card.classList.add('loading');
        card.style.animationDelay = `${index * 0.1}s`;
        observer.observe(card);
    });
});

// Header scroll effect
window.addEventListener('scroll', () => {
    const header = document.querySelector('.header');
    if (window.scrollY > 100) {
        header.style.background = 'rgba(255, 255, 255, 0.98)';
        header.style.boxShadow = '0 2px 20px rgba(0, 0, 0, 0.1)';
    } else {
        header.style.background = 'rgba(255, 255, 255, 0.95)';
        header.style.boxShadow = 'none';
    }
});

// Add CSS animation keyframes
const style = document.createElement('style');
style.textContent = `
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
`;
document.head.appendChild(style);

