



def get_url():                
    contents = requests.get('https://random.dog/woof.json').json()
    url = contents['url']                                                                      
    return url


def get_image_url():
    allowed_extension = ['jpg','jpeg','png']
    file_extension = ''
    while file_extension not in allowed_extension:
        url = get_url()
        file_extension = re.search("([^.]*)$",url).group(1).lower()
    return url


@dp.message_handler(commands=['bop'])
async def process_photo_command(message: types.Message):
    caption = 'Ути-пути'
    image = get_image_url()
    await bot.send_photo(message.from_user.id, image,
                         caption=caption,
                         reply_to_message_id=message.message_id)
