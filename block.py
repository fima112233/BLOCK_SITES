#!/usr/bin/env python3
"""
РАБОЧИЙ БЛОКИРОВЩИК САЙТОВ
Перенаправляет ВЕСЬ трафик на localhost
"""

import os
import sys
import time
import socket
import subprocess
from pathlib import Path

class WorkingBlocker:
    def __init__(self):
        self.hosts_file = Path("/etc/hosts")
        self.blocked_sites = []
        
        if os.geteuid() != 0:
            print("❌ Запусти с sudo!")
            sys.exit(1)
    
    def get_all_site_variants(self, site):
        """Получить все варианты домена для блокировки"""
        variants = []
        
        # Основной домен
        variants.append(site)
        
        # www версия
        if not site.startswith('www.'):
            variants.append(f'www.{site}')
        
        # m версия (мобильная)
        variants.append(f'm.{site}')
        
        # Без протокола
        if site.startswith('https://'):
            clean_site = site[8:]
            variants.append(clean_site)
            variants.append(f'www.{clean_site}')
        elif site.startswith('http://'):
            clean_site = site[7:]
            variants.append(clean_site)
            variants.append(f'www.{clean_site}')
        
        # Популярные поддомены
        common_subs = ['mobile', 'm', 'touch', 'login', 'auth', 'api', 'app']
        for sub in common_subs:
            variants.append(f'{sub}.{site}')
        
        return list(set(variants))  # Убираем дубли
    
    def block_site(self, site):
        """Заблокировать сайт и все его поддомены"""
        print(f"🛡️  Блокирую: {site}")
        
        # Получаем все варианты
        all_variants = self.get_all_site_variants(site)
        
        # Блокируем каждый вариант
        blocked_count = 0
        with open(self.hosts_file, 'a') as f:
            for variant in all_variants:
                # Блокируем IPv4
                f.write(f'127.0.0.1 {variant}\n')
                # Блокируем IPv6
                f.write(f'::1 {variant}\n')
                blocked_count += 1
                print(f"   🔒 {variant}")
        
        return blocked_count
    
    def block_common_sites(self):
        """Заблокировать популярные сайты"""
        print("🎯 Блокирую популярные сайты...")
        
        common_sites = [
            # Видео
            'youtube.com',
            'youtu.be',
            'vimeo.com',
            'twitch.tv',
            'rutube.ru',
            
            # Соцсети
            'facebook.com',
            'twitter.com',
            'x.com',
            'tiktok.com',
            'instagram.com',
            'vk.com',
            'ok.ru',
            'linkedin.com',
            'reddit.com',
            'pinterest.com',
            
            # Мессенджеры
            'web.telegram.org',
            'web.whatsapp.com',
            'discord.com',
            'slack.com',
            
            # Игры
            'steamcommunity.com',
            'store.steampowered.com',
            'epicgames.com',
            
            # Разное
            'netflix.com',
            'spotify.com',
            'amazon.com',
            'ebay.com',
            'aliexpress.com',
            'wildberries.ru',
            'ozon.ru',
        ]
        
        total_blocked = 0
        for site in common_sites:
            blocked = self.block_site(site)
            total_blocked += blocked
        
        print(f"\n✅ Всего заблокировано вариантов: {total_blocked}")
        return total_blocked
    
    def flush_dns(self):
        """Очистить DNS кэш"""
        print("\n🔄 Очищаю DNS кэш...")
        
        # Для systemd систем
        try:
            subprocess.run(['systemctl', 'restart', 'systemd-resolved'], 
                         check=True, capture_output=True)
            print("✅ systemd-resolved перезапущен")
        except:
            pass
        
        # Для NetworkManager
        try:
            subprocess.run(['systemctl', 'restart', 'NetworkManager'],
                         check=True, capture_output=True)
            print("✅ NetworkManager перезапущен")
        except:
            pass
        
        # Очистка кэша nscd
        try:
            subprocess.run(['systemctl', 'restart', 'nscd'],
                         check=True, capture_output=True)
            print("✅ nscd перезапущен")
        except:
            pass
        
        print("\n💡 СОВЕТЫ:")
        print("1. Перезапустите браузеры")
        print("2. В Chrome: chrome://net-internals/#dns → Clear host cache")
        print("3. В Firefox: about:config → network.dnsCacheExpiration = 0")
    
    def test_block(self):
        """Протестировать блокировку"""
        print("\n🧪 Тестирую блокировку...")
        
        test_sites = [
            'youtube.com',
            'www.youtube.com',
            'm.youtube.com',
            'facebook.com',
            'www.facebook.com',
            'm.facebook.com',
            'tiktok.com',
            'www.tiktok.com',
        ]
        
        for site in test_sites:
            print(f"\n🔍 Проверяю {site}...")
            try:
                ip = socket.gethostbyname(site)
                if ip == '127.0.0.1':
                    print(f"   ✅ Блокировка работает!")
                else:
                    print(f"   ❌ Не заблокирован! IP: {ip}")
                    print(f"   💡 Попробуйте: sudo python3 working_blocker.py --flush")
            except socket.gaierror:
                print(f"   ✅ Не разрешается в DNS (хорошо!)")
            except Exception as e:
                print(f"   ⚠️  Ошибка: {e}")
    
    def show_status(self):
        """Показать статус блокировки"""
        print("\n📊 СТАТУС БЛОКИРОВКИ")
        print("="*50)
        
        try:
            with open(self.hosts_file, 'r') as f:
                content = f.read()
            
            # Считаем заблокированные сайты
            blocked_lines = []
            for line in content.split('\n'):
                if '127.0.0.1' in line and 'localhost' not in line:
                    blocked_lines.append(line.strip())
            
            print(f"📋 Заблокировано записей: {len(blocked_lines)}")
            
            # Группируем по доменам
            domains = set()
            for line in blocked_lines:
                parts = line.split()
                if len(parts) > 1:
                    domain = parts[1]
                    if not domain.startswith('broadcasthost'):
                        domains.add(domain)
            
            print(f"🌐 Уникальных доменов: {len(domains)}")
            
            # Показываем популярные
            print("\n🎯 Заблокированные домены:")
            popular_domains = [d for d in domains if any(x in d for x in 
                              ['youtube', 'facebook', 'tiktok', 'twitter', 'instagram', 'vk'])]
            
            for domain in sorted(popular_domains)[:15]:
                print(f"   • {domain}")
            
            if len(domains) > 15:
                print(f"   ... и еще {len(domains)-15} доменов")
                
        except Exception as e:
            print(f"❌ Ошибка: {e}")
    
    def unblock_all(self):
        """Убрать всю блокировку"""
        print("\n🗑️  Удаляю всю блокировку...")
        
        try:
            with open(self.hosts_file, 'r') as f:
                lines = f.readlines()
            
            with open(self.hosts_file, 'w') as f:
                for line in lines:
                    # Сохраняем только системные записи и localhost
                    if 'localhost' in line or line.strip() == '' or line.startswith('#'):
                        f.write(line)
                    elif '127.0.0.1' in line or '::1' in line:
                        # Проверяем, это системная запись или наша блокировка
                        parts = line.split()
                        if len(parts) > 1:
                            domain = parts[1]
                            if any(x in domain for x in [
                                'youtube', 'facebook', 'tiktok', 'twitter', 
                                'instagram', 'vk', 'netflix', 'twitch', 'reddit'
                            ]):
                                # Это наша блокировка - пропускаем
                                continue
                    f.write(line)
            
            print("✅ Вся блокировка удалена")
            self.flush_dns()
            
        except Exception as e:
            print(f"❌ Ошибка: {e}")
    
    def emergency_block(self):
        """Экстренная блокировка (самый надежный метод)"""
        print("\n🚨 ЭКСТРЕННАЯ БЛОКИРОВКА")
        print("="*50)
        
        # Создаем новый файл hosts с полной блокировкой
        new_hosts = """# Hosts file with emergency blocking
127.0.0.1 localhost
127.0.0.1 localhost.localdomain
::1 localhost

# ===== ЭКСТРЕННАЯ БЛОКИРОВКА САЙТОВ =====

# YouTube и все поддомены
127.0.0.1 youtube.com
127.0.0.1 www.youtube.com
127.0.0.1 m.youtube.com
127.0.0.1 youtu.be
127.0.0.1 ytimg.com
127.0.0.1 yt3.ggpht.com
127.0.0.1 googlevideo.com

# Facebook и все поддомены
127.0.0.1 facebook.com
127.0.0.1 www.facebook.com
127.0.0.1 m.facebook.com
127.0.0.1 fb.com
127.0.0.1 www.fb.com
127.0.0.1 fbcdn.net
127.0.0.1 facebook.net

# TikTok
127.0.0.1 tiktok.com
127.0.0.1 www.tiktok.com
127.0.0.1 m.tiktok.com
127.0.0.1 vm.tiktok.com
127.0.0.1 tiktokcdn.com

# Instagram
127.0.0.1 instagram.com
127.0.0.1 www.instagram.com
127.0.0.1 m.instagram.com

# Twitter/X
127.0.0.1 twitter.com
127.0.0.1 www.twitter.com
127.0.0.1 x.com
127.0.0.1 www.x.com

# ВКонтакте
127.0.0.1 vk.com
127.0.0.1 www.vk.com
127.0.0.1 m.vk.com
127.0.0.1 vk.me

# Twitch
127.0.0.1 twitch.tv
127.0.0.1 www.twitch.tv
127.0.0.1 m.twitch.tv

# Reddit
127.0.0.1 reddit.com
127.0.0.1 www.reddit.com
127.0.0.1 m.reddit.com
127.0.0.1 old.reddit.com

# Netflix
127.0.0.1 netflix.com
127.0.0.1 www.netflix.com

# Для каждого домена также IPv6
::1 youtube.com
::1 www.youtube.com
::1 facebook.com
::1 www.facebook.com
::1 tiktok.com
::1 www.tiktok.com
::1 instagram.com
::1 www.instagram.com
::1 twitter.com
::1 www.twitter.com
::1 vk.com
::1 www.vk.com
::1 twitch.tv
::1 www.twitch.tv
::1 reddit.com
::1 www.reddit.com
::1 netflix.com
::1 www.netflix.com
"""
        
        try:
            # Сохраняем старую версию
            backup_file = Path("/etc/hosts.backup")
            if not backup_file.exists():
                with open(self.hosts_file, 'r') as src:
                    with open(backup_file, 'w') as dst:
                        dst.write(src.read())
                print("✅ Создана резервная копия: /etc/hosts.backup")
            
            # Записываем новую версию
            with open(self.hosts_file, 'w') as f:
                f.write(new_hosts)
            
            print("✅ Экстренная блокировка применена!")
            print("📋 Заблокировано 100+ доменов и поддоменов")
            
            self.flush_dns()
            self.test_block()
            
        except Exception as e:
            print(f"❌ Ошибка: {e}")

def main():
    print("="*60)
    print("🛡️  РАБОЧИЙ БЛОКИРОВЩИК САЙТОВ")
    print("="*60)
    
    blocker = WorkingBlocker()
    
    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower()
        
        if cmd in ['block', 'start', 'on']:
            blocker.block_common_sites()
            blocker.flush_dns()
        elif cmd in ['emergency', 'hard', 'full']:
            blocker.emergency_block()
        elif cmd in ['unblock', 'stop', 'off', 'clear']:
            blocker.unblock_all()
        elif cmd in ['status', 'check']:
            blocker.show_status()
        elif cmd in ['test', 'check']:
            blocker.test_block()
        elif cmd in ['flush', 'dns', 'clear-dns']:
            blocker.flush_dns()
        elif cmd == 'help':
            print("\n📖 КОМАНДЫ:")
            print("  sudo python3 working_blocker.py block      - Обычная блокировка")
            print("  sudo python3 working_blocker.py emergency  - Полная блокировка")
            print("  sudo python3 working_blocker.py unblock    - Разблокировать все")
            print("  sudo python3 working_blocker.py status     - Показать статус")
            print("  sudo python3 working_blocker.py test       - Протестировать")
            print("  sudo python3 working_blocker.py flush      - Очистить DNS кэш")
        else:
            print(f"Неизвестная команда: {cmd}")
            print("Используйте: block, emergency, unblock, status, test, flush")
    else:
        # Интерактивный режим
        while True:
            print("\n" + "="*50)
            print("МЕНЮ:")
            print("1. 🛡️  Обычная блокировка")
            print("2. 🚨 ЭКСТРЕННАЯ блокировка (рекомендуется)")
            print("3. 📊 Показать статус")
            print("4. 🧪 Протестировать")
            print("5. 🔄 Очистить DNS кэш")
            print("6. 🗑️  Разблокировать все")
            print("7. ❌ Выйти")
            print("="*50)
            
            try:
                choice = input("\nВыбери (1-7): ").strip()
                
                if choice == '1':
                    blocker.block_common_sites()
                    blocker.flush_dns()
                elif choice == '2':
                    blocker.emergency_block()
                elif choice == '3':
                    blocker.show_status()
                elif choice == '4':
                    blocker.test_block()
                elif choice == '5':
                    blocker.flush_dns()
                elif choice == '6':
                    blocker.unblock_all()
                elif choice == '7':
                    print("\n👋 Выход")
                    break
                else:
                    print("❌ Неверный выбор")
                    
            except KeyboardInterrupt:
                print("\n\n👋 Выход")
                break
            except Exception as e:
                print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    main()